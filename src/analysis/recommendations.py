"""
Event Recommendation System

Automatically generates recommendations for events based on:
- Scheduling conflicts
- Venue availability
- Time optimization
- Building usage patterns
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

sys.path.append(str(Path(__file__).parent.parent))
from database.db_utils import get_db_connection
from analysis.conflict_detection import (
    detect_venue_conflicts,
    detect_building_conflicts,
    suggest_alternative_slots,
    get_all_bookings_for_location,
    parse_event_datetime
)


def generate_event_recommendations(event_id: int) -> Dict:
    """
    Generate recommendations for a specific event
    
    Args:
        event_id: The event ID to generate recommendations for
    
    Returns:
        Dictionary containing recommendations
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get event details
    cursor.execute('''
        SELECT id, title, date, time, location
        FROM events
        WHERE id = ?
    ''', (event_id,))
    
    result = cursor.fetchone()
    if not result:
        return {}
    
    event_id, title, date, time, location = result
    
    recommendations = {
        'event_id': event_id,
        'has_conflicts': False,
        'conflict_type': None,
        'severity': 'none',  # none, low, medium, high
        'recommended_action': None,
        'alternative_times': [],
        'details': None
    }
    
    # Check for venue conflicts
    venue_conflicts = detect_venue_conflicts()
    for conflict in venue_conflicts:
        if event_id in [conflict['event1_id'], conflict['event2_id']]:
            recommendations['has_conflicts'] = True
            recommendations['conflict_type'] = 'venue_double_booking'
            recommendations['severity'] = 'high'
            
            # Get alternative time slots
            if location and date:
                conflicting_times = get_all_bookings_for_location(location, date, exclude_event_id=event_id)
                alternatives = suggest_alternative_slots(location, date, conflicting_times)
                
                if alternatives:
                    # Get the first available slot
                    best_slot = alternatives[0]
                    recommendations['recommended_action'] = f"Move to {best_slot['slot']}"
                    recommendations['alternative_times'] = [alt['slot'] for alt in alternatives[:3]]  # Top 3
                    recommendations['details'] = f"Venue '{location}' is double-booked. Recommend rescheduling to {best_slot['slot']}."
                else:
                    recommendations['recommended_action'] = "Find alternative venue"
                    recommendations['details'] = f"Venue '{location}' is double-booked with no available slots on this date."
            break
    
    # Check for building conflicts (if no venue conflict found)
    if not recommendations['has_conflicts']:
        building_conflicts = detect_building_conflicts()
        for conflict in building_conflicts:
            if event_id in [e['event_id'] for e in conflict['events']]:
                recommendations['has_conflicts'] = True
                recommendations['conflict_type'] = 'building_conflict'
                recommendations['severity'] = 'medium'
                
                # Extract building name from location
                if location:
                    building = location.split(',')[0].strip() if ',' in location else location.split('-')[0].strip()
                    
                    # Get all bookings for this building on this date
                    cursor.execute('''
                        SELECT id, time, location
                        FROM events
                        WHERE date = ? 
                        AND id != ?
                        AND (location LIKE ? OR location LIKE ?)
                    ''', (date, event_id, f"{building},%", f"{building} %"))
                    
                    building_events = cursor.fetchall()
                    conflicting_times = []
                    
                    for _, event_time, _ in building_events:
                        if event_time:
                            start, end = parse_event_datetime(date, event_time)
                            if start and end:
                                conflicting_times.append((start, end))
                    
                    # Suggest alternatives
                    if conflicting_times:
                        alternatives = suggest_alternative_slots(location, date, conflicting_times)
                        if alternatives:
                            best_slot = alternatives[0]
                            recommendations['recommended_action'] = f"Consider moving to {best_slot['slot']}"
                            recommendations['alternative_times'] = [alt['slot'] for alt in alternatives[:3]]
                            recommendations['details'] = f"Multiple events scheduled in {building}. Consider spacing out events."
                break
    
    # If no conflicts, check for optimization opportunities
    if not recommendations['has_conflicts'] and time:
        # Check if event is during peak hours
        event_hour = int(time.split(':')[0])
        
        # Peak hours: 10 AM - 2 PM
        if 10 <= event_hour < 14:
            recommendations['severity'] = 'low'
            recommendations['recommended_action'] = "Consider off-peak hours for better attendance"
            recommendations['details'] = "Event scheduled during peak hours. Consider early morning or late afternoon for less competition."
    
    conn.close()
    return recommendations


def save_recommendations_to_db(event_id: int, recommendations: Dict):
    """
    Save recommendations to the database
    
    Args:
        event_id: The event ID
        recommendations: Dictionary of recommendations
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Delete existing recommendations for this event
    cursor.execute('DELETE FROM event_recommendations WHERE event_id = ?', (event_id,))
    
    # Insert new recommendations
    cursor.execute('''
        INSERT INTO event_recommendations (
            event_id,
            has_conflicts,
            conflict_type,
            severity,
            recommended_action,
            alternative_times,
            details,
            generated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, DATETIME('now'))
    ''', (
        event_id,
        1 if recommendations.get('has_conflicts') else 0,
        recommendations.get('conflict_type'),
        recommendations.get('severity', 'none'),
        recommendations.get('recommended_action'),
        ', '.join(recommendations.get('alternative_times', [])) if recommendations.get('alternative_times') else None,
        recommendations.get('details')
    ))
    
    conn.commit()
    conn.close()


def generate_all_recommendations():
    """Generate recommendations for all events"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all upcoming events
    cursor.execute('''
        SELECT id FROM events
        WHERE date >= DATE('now')
        ORDER BY date, time
    ''')
    
    event_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    print(f"\nGenerating recommendations for {len(event_ids)} events...")
    
    recommendations_count = {
        'total': len(event_ids),
        'with_conflicts': 0,
        'high_severity': 0,
        'medium_severity': 0,
        'low_severity': 0
    }
    
    for event_id in event_ids:
        recommendations = generate_event_recommendations(event_id)
        save_recommendations_to_db(event_id, recommendations)
        
        if recommendations.get('has_conflicts'):
            recommendations_count['with_conflicts'] += 1
        
        severity = recommendations.get('severity', 'none')
        if severity == 'high':
            recommendations_count['high_severity'] += 1
        elif severity == 'medium':
            recommendations_count['medium_severity'] += 1
        elif severity == 'low':
            recommendations_count['low_severity'] += 1
    
    print(f"\nRecommendation Generation Summary:")
    print(f"  Total events: {recommendations_count['total']}")
    print(f"  Events with conflicts: {recommendations_count['with_conflicts']}")
    print(f"  High severity: {recommendations_count['high_severity']}")
    print(f"  Medium severity: {recommendations_count['medium_severity']}")
    print(f"  Low severity: {recommendations_count['low_severity']}")
    
    return recommendations_count


def get_event_recommendations(event_id: int) -> Optional[Dict]:
    """
    Retrieve recommendations for a specific event from the database
    
    Args:
        event_id: The event ID
    
    Returns:
        Dictionary of recommendations or None
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            has_conflicts,
            conflict_type,
            severity,
            recommended_action,
            alternative_times,
            details,
            generated_at
        FROM event_recommendations
        WHERE event_id = ?
    ''', (event_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return None
    
    has_conflicts, conflict_type, severity, recommended_action, alternative_times, details, generated_at = result
    
    return {
        'event_id': event_id,
        'has_conflicts': bool(has_conflicts),
        'conflict_type': conflict_type,
        'severity': severity,
        'recommended_action': recommended_action,
        'alternative_times': alternative_times.split(', ') if alternative_times else [],
        'details': details,
        'generated_at': generated_at
    }


def display_event_with_recommendations(event_id: int):
    """Display event details with recommendations"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get event details
    cursor.execute('''
        SELECT title, date, time, location, description
        FROM events
        WHERE id = ?
    ''', (event_id,))
    
    event = cursor.fetchone()
    if not event:
        print(f"Event {event_id} not found")
        return
    
    title, date, time, location, description = event
    
    print(f"\n{'='*80}")
    print(f"Event: {title}")
    print(f"{'='*80}")
    print(f"Date: {date}")
    print(f"Time: {time if time else 'Not specified'}")
    print(f"Location: {location if location else 'Not specified'}")
    
    # Get recommendations
    recommendations = get_event_recommendations(event_id)
    
    if recommendations:
        print(f"\n{'─'*80}")
        print("RECOMMENDATIONS")
        print(f"{'─'*80}")
        
        if recommendations['has_conflicts']:
            severity_symbols = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢',
                'none': '⚪'
            }
            symbol = severity_symbols.get(recommendations['severity'], '')
            
            print(f"Severity: {symbol} {recommendations['severity'].upper()}")
            print(f"Conflict Type: {recommendations['conflict_type'].replace('_', ' ').title()}")
            
            if recommendations['recommended_action']:
                print(f"\nRecommended Action: {recommendations['recommended_action']}")
            
            if recommendations['alternative_times']:
                print(f"\nAlternative Time Slots:")
                for i, time_slot in enumerate(recommendations['alternative_times'], 1):
                    print(f"  {i}. {time_slot}")
            
            if recommendations['details']:
                print(f"\nDetails: {recommendations['details']}")
        else:
            print("✓ No conflicts detected - event is optimally scheduled")
        
        print(f"\nLast updated: {recommendations['generated_at']}")
    else:
        print("\nNo recommendations available. Run recommendation generation to create them.")
    
    print(f"{'='*80}\n")
    
    conn.close()


if __name__ == "__main__":
    # Generate recommendations for all events
    generate_all_recommendations()
