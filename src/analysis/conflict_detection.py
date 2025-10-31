"""
Event Conflict Detection System

This module identifies scheduling conflicts including:
- Venue double-bookings
- Time overlaps for recurring events
- Scheduling conflicts within the same building
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from database.db_utils import get_db_connection


def parse_event_datetime(date_str, time_str):
    """Parse event date and time strings into datetime objects"""
    try:
        # Parse date
        event_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        if not time_str:
            # If no time specified, assume all-day event (00:00 to 23:59)
            start_dt = datetime.combine(event_date, datetime.min.time())
            end_dt = datetime.combine(event_date, datetime.max.time())
            return start_dt, end_dt
        
        # Parse time (format: HH:MM)
        event_time = datetime.strptime(time_str, '%H:%M').time()
        start_dt = datetime.combine(event_date, event_time)
        
        # Assume 1-hour duration for events with time but no end time
        end_dt = start_dt + timedelta(hours=1)
        
        return start_dt, end_dt
    except (ValueError, TypeError) as e:
        return None, None


def check_time_overlap(start1, end1, start2, end2):
    """Check if two time ranges overlap"""
    if not all([start1, end1, start2, end2]):
        return False
    
    # Two events overlap if one starts before the other ends
    return start1 < end2 and start2 < end1


def suggest_alternative_slots(location, date, conflicting_times):
    """
    Suggest alternative time slots for an event based on existing bookings
    
    Args:
        location: The venue location
        date: The date (YYYY-MM-DD) for the event
        conflicting_times: List of (start, end) datetime tuples that are already booked
    
    Returns:
        List of suggested alternative time slots
    """
    suggestions = []
    
    # Define standard time slots for campus events
    standard_slots = [
        (8, 0, 9, 0),   # 8:00 AM - 9:00 AM
        (9, 0, 10, 0),  # 9:00 AM - 10:00 AM
        (10, 0, 11, 0), # 10:00 AM - 11:00 AM
        (11, 0, 12, 0), # 11:00 AM - 12:00 PM
        (12, 0, 13, 0), # 12:00 PM - 1:00 PM
        (13, 0, 14, 0), # 1:00 PM - 2:00 PM
        (14, 0, 15, 0), # 2:00 PM - 3:00 PM
        (15, 0, 16, 0), # 3:00 PM - 4:00 PM
        (16, 0, 17, 0), # 4:00 PM - 5:00 PM
        (17, 0, 18, 0), # 5:00 PM - 6:00 PM
        (18, 0, 19, 0), # 6:00 PM - 7:00 PM
    ]
    
    event_date = datetime.strptime(date, '%Y-%m-%d').date()
    
    # Check each standard slot
    for start_h, start_m, end_h, end_m in standard_slots:
        slot_start = datetime.combine(event_date, datetime.min.time().replace(hour=start_h, minute=start_m))
        slot_end = datetime.combine(event_date, datetime.min.time().replace(hour=end_h, minute=end_m))
        
        # Check if this slot conflicts with any existing bookings
        is_available = True
        for conflict_start, conflict_end in conflicting_times:
            if check_time_overlap(slot_start, slot_end, conflict_start, conflict_end):
                is_available = False
                break
        
        if is_available:
            suggestions.append({
                'time': f"{start_h:02d}:{start_m:02d}",
                'end_time': f"{end_h:02d}:{end_m:02d}",
                'slot': f"{start_h:02d}:{start_m:02d} - {end_h:02d}:{end_m:02d}"
            })
    
    return suggestions


def get_all_bookings_for_location(location, date):
    """Get all event bookings for a specific location and date"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, title, time
        FROM events
        WHERE location LIKE ?
        AND date = ?
        ORDER BY time
    """, (f'%{location}%', date))
    
    events = cursor.fetchall()
    bookings = []
    
    for event_id, title, time in events:
        start, end = parse_event_datetime(date, time)
        if start and end:
            bookings.append((start, end, title))
    
    conn.close()
    return bookings


def detect_venue_conflicts():
    """
    Detect double-bookings in the same venue
    Returns a list of conflicts with event details
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all events with location, date, and time
    cursor.execute("""
        SELECT id, title, date, time, location
        FROM events
        WHERE location IS NOT NULL 
        AND location != ''
        AND date >= date('now')
        ORDER BY location, date, time
    """)
    
    events = cursor.fetchall()
    conflicts = []
    
    # Check for conflicts by comparing events at the same location
    for i in range(len(events)):
        event1_id, title1, date1, time1, location1 = events[i]
        start1, end1 = parse_event_datetime(date1, time1)
        
        if not start1:
            continue
        
        for j in range(i + 1, len(events)):
            event2_id, title2, date2, time2, location2 = events[j]
            
            # Only check events at the same location
            if location1.strip().lower() != location2.strip().lower():
                continue
            
            start2, end2 = parse_event_datetime(date2, time2)
            
            if not start2:
                continue
            
            # Check for time overlap
            if check_time_overlap(start1, end1, start2, end2):
                # Get all bookings for this location on this date to suggest alternatives
                all_bookings = get_all_bookings_for_location(location1, date1)
                conflicting_times = [(start, end) for start, end, _ in all_bookings]
                
                # Suggest alternative time slots
                alternatives = suggest_alternative_slots(location1, date1, conflicting_times)
                
                # Create specific recommendations for each event
                recommendation = None
                if alternatives:
                    # Recommend moving the later event to the first available slot
                    first_slot = alternatives[0]
                    later_event = 'event2' if start2 > start1 else 'event1'
                    later_title = title2 if start2 > start1 else title1
                    recommendation = f"Recommend moving '{later_title}' to {first_slot['slot']}"
                
                conflicts.append({
                    'type': 'venue_conflict',
                    'location': location1,
                    'event1': {
                        'id': event1_id,
                        'title': title1,
                        'date': date1,
                        'time': time1,
                        'start': start1,
                        'end': end1
                    },
                    'event2': {
                        'id': event2_id,
                        'title': title2,
                        'date': date2,
                        'time': time2,
                        'start': start2,
                        'end': end2
                    },
                    'alternative_slots': alternatives[:3],  # Show top 3 alternatives
                    'recommendation': recommendation
                })
    
    conn.close()
    return conflicts


def detect_building_conflicts():
    """
    Detect conflicts within the same building (Bldg X)
    Returns conflicts where multiple events occur in different rooms of the same building
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, title, date, time, location
        FROM events
        WHERE location LIKE 'Bldg%'
        AND date >= date('now')
        ORDER BY date, time
    """)
    
    events = cursor.fetchall()
    building_events = {}
    
    # Group events by building and time
    for event_id, title, date, time, location in events:
        # Extract building number (e.g., "Bldg 10" -> "10")
        building = location.split(',')[0].strip() if ',' in location else location.strip()
        
        start, end = parse_event_datetime(date, time)
        if not start:
            continue
        
        key = (building, date)
        if key not in building_events:
            building_events[key] = []
        
        building_events[key].append({
            'id': event_id,
            'title': title,
            'date': date,
            'time': time,
            'location': location,
            'start': start,
            'end': end
        })
    
    # Find concurrent events in the same building
    building_conflicts = []
    for (building, date), event_list in building_events.items():
        if len(event_list) > 1:
            # Check for time overlaps
            for i in range(len(event_list)):
                for j in range(i + 1, len(event_list)):
                    event1 = event_list[i]
                    event2 = event_list[j]
                    
                    if check_time_overlap(event1['start'], event1['end'], 
                                        event2['start'], event2['end']):
                        building_conflicts.append({
                            'type': 'building_conflict',
                            'building': building,
                            'date': date,
                            'event1': event1,
                            'event2': event2
                        })
    
    conn.close()
    return building_conflicts


def detect_recurring_conflicts():
    """
    Detect conflicts in recurring events (events with the same title)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Find events with the same title
    cursor.execute("""
        SELECT title, COUNT(*) as count
        FROM events
        WHERE date >= date('now')
        GROUP BY title
        HAVING count > 1
        ORDER BY count DESC
    """)
    
    recurring_titles = cursor.fetchall()
    conflicts = []
    
    for title, count in recurring_titles:
        # Get all instances of this recurring event
        cursor.execute("""
            SELECT id, title, date, time, location
            FROM events
            WHERE title = ?
            AND date >= date('now')
            ORDER BY date, time
        """, (title,))
        
        instances = cursor.fetchall()
        
        # Check for timing issues (e.g., too close together)
        for i in range(len(instances) - 1):
            event1_id, title1, date1, time1, location1 = instances[i]
            event2_id, title2, date2, time2, location2 = instances[i + 1]
            
            start1, end1 = parse_event_datetime(date1, time1)
            start2, end2 = parse_event_datetime(date2, time2)
            
            if not start1 or not start2:
                continue
            
            # Check if events are less than 30 minutes apart (potential conflict)
            time_diff = (start2 - end1).total_seconds() / 60  # minutes
            
            if time_diff < 30 and time_diff > 0:
                conflicts.append({
                    'type': 'recurring_timing_conflict',
                    'title': title,
                    'warning': f'Events only {int(time_diff)} minutes apart',
                    'event1': {
                        'id': event1_id,
                        'date': date1,
                        'time': time1,
                        'location': location1
                    },
                    'event2': {
                        'id': event2_id,
                        'date': date2,
                        'time': time2,
                        'location': location2
                    }
                })
    
    conn.close()
    return conflicts


def get_all_conflicts():
    """
    Run all conflict detection checks and return combined results
    """
    conflicts = {
        'venue_conflicts': detect_venue_conflicts(),
        'building_conflicts': detect_building_conflicts(),
        'recurring_conflicts': detect_recurring_conflicts()
    }
    
    # Calculate summary statistics
    total_conflicts = (
        len(conflicts['venue_conflicts']) +
        len(conflicts['building_conflicts']) +
        len(conflicts['recurring_conflicts'])
    )
    
    conflicts['summary'] = {
        'total': total_conflicts,
        'venue': len(conflicts['venue_conflicts']),
        'building': len(conflicts['building_conflicts']),
        'recurring': len(conflicts['recurring_conflicts'])
    }
    
    return conflicts


def format_conflict_report(conflicts):
    """Format conflicts into a readable report"""
    report = []
    report.append("=" * 80)
    report.append("EVENT CONFLICT DETECTION REPORT")
    report.append("=" * 80)
    report.append("")
    
    summary = conflicts['summary']
    report.append(f"Total Conflicts Found: {summary['total']}")
    report.append(f"  - Venue Double-Bookings: {summary['venue']}")
    report.append(f"  - Building Conflicts: {summary['building']}")
    report.append(f"  - Recurring Event Issues: {summary['recurring']}")
    report.append("")
    
    # Venue Conflicts
    if conflicts['venue_conflicts']:
        report.append("-" * 80)
        report.append("VENUE DOUBLE-BOOKINGS")
        report.append("-" * 80)
        for conflict in conflicts['venue_conflicts']:
            report.append(f"\nLocation: {conflict['location']}")
            report.append(f"  Event 1: {conflict['event1']['title']}")
            report.append(f"    Date/Time: {conflict['event1']['date']} at {conflict['event1']['time'] or 'All Day'}")
            report.append(f"  Event 2: {conflict['event2']['title']}")
            report.append(f"    Date/Time: {conflict['event2']['date']} at {conflict['event2']['time'] or 'All Day'}")
            report.append(f"  ⚠️  CONFLICT: Both events scheduled in the same location at overlapping times")
            
            # Add specific recommendation
            if conflict.get('recommendation'):
                report.append(f"\n  🎯 RECOMMENDATION: {conflict['recommendation']}")
            
            # Add alternative time slot suggestions
            if conflict.get('alternative_slots'):
                report.append(f"\n  💡 ALL AVAILABLE TIME SLOTS FOR THIS VENUE:")
                for alt in conflict['alternative_slots']:
                    report.append(f"     • {alt['slot']}")
            else:
                report.append(f"\n  ℹ️  No available alternative time slots found for this date")
        report.append("")
    
    # Building Conflicts
    if conflicts['building_conflicts']:
        report.append("-" * 80)
        report.append("BUILDING CONFLICTS (Multiple Events in Same Building)")
        report.append("-" * 80)
        for conflict in conflicts['building_conflicts']:
            report.append(f"\nBuilding: {conflict['building']}")
            report.append(f"Date: {conflict['date']}")
            report.append(f"  Event 1: {conflict['event1']['title']}")
            report.append(f"    Location: {conflict['event1']['location']}")
            report.append(f"    Time: {conflict['event1']['time'] or 'All Day'}")
            report.append(f"  Event 2: {conflict['event2']['title']}")
            report.append(f"    Location: {conflict['event2']['location']}")
            report.append(f"    Time: {conflict['event2']['time'] or 'All Day'}")
            report.append(f"  ℹ️  Note: Multiple events in same building at similar times")
        report.append("")
    
    # Recurring Conflicts
    if conflicts['recurring_conflicts']:
        report.append("-" * 80)
        report.append("RECURRING EVENT TIMING ISSUES")
        report.append("-" * 80)
        for conflict in conflicts['recurring_conflicts']:
            report.append(f"\nEvent Series: {conflict['title']}")
            report.append(f"  Instance 1: {conflict['event1']['date']} at {conflict['event1']['time']}")
            report.append(f"    Location: {conflict['event1']['location']}")
            report.append(f"  Instance 2: {conflict['event2']['date']} at {conflict['event2']['time']}")
            report.append(f"    Location: {conflict['event2']['location']}")
            report.append(f"  ⚠️  {conflict['warning']}")
        report.append("")
    
    if summary['total'] == 0:
        report.append("✅ No conflicts detected! All events are properly scheduled.")
        report.append("")
    
    report.append("=" * 80)
    
    return "\n".join(report)


def run_conflict_detection():
    """Main function to run conflict detection and display results"""
    print("\nRunning Event Conflict Detection...")
    print("=" * 80)
    
    conflicts = get_all_conflicts()
    report = format_conflict_report(conflicts)
    
    print(report)
    
    return conflicts
    return conflicts


if __name__ == "__main__":
    run_conflict_detection()
