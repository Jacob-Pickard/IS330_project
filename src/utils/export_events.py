"""
Event Export Module

Provides export capabilities for events including:
- iCal (.ics) format for calendar applications
- CSV format for data analysis
- Bulk export with filtering
"""

import csv
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

sys.path.append(str(Path(__file__).parent.parent))
from database.db_utils import get_db_connection
from database.error_handling import logger, with_error_handling

try:
    from icalendar import Calendar, Event as ICalEvent
    ICAL_AVAILABLE = True
except ImportError:
    ICAL_AVAILABLE = False
    logger.warning("icalendar library not installed. iCal export will not be available.")


@with_error_handling("CSV Export")
def export_to_csv(
    output_file: str = "events_export.csv",
    event_type: Optional[str] = None,
    location: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    include_enhanced: bool = True
) -> int:
    """
    Export events to CSV format
    
    Args:
        output_file: Path to output CSV file
        event_type: Filter by event type
        location: Filter by location
        date_from: Filter events from date (YYYY-MM-DD)
        date_to: Filter events to date (YYYY-MM-DD)
        include_enhanced: Include enhanced content fields
    
    Returns:
        Number of events exported
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Build query with filters
    if include_enhanced:
        query = '''
            SELECT 
                e.id,
                e.title,
                e.date,
                e.time,
                e.location,
                e.description,
                e.link,
                ec.event_type,
                ec.seo_score,
                ec.enhanced_description,
                GROUP_CONCAT(et.tag, ', ') as tags
            FROM events e
            LEFT JOIN enhanced_content ec ON e.id = ec.event_id
            LEFT JOIN event_tags et ON e.id = et.event_id
            WHERE e.date >= DATE('now')
        '''
    else:
        query = '''
            SELECT 
                e.id,
                e.title,
                e.date,
                e.time,
                e.location,
                e.description,
                e.link
            FROM events e
            WHERE e.date >= DATE('now')
        '''
    
    params = []
    
    # Add filters
    if date_from:
        query += ' AND e.date >= ?'
        params.append(date_from)
    if date_to:
        query += ' AND e.date <= ?'
        params.append(date_to)
    if event_type and include_enhanced:
        query += ' AND ec.event_type LIKE ?'
        params.append(f'%{event_type}%')
    if location:
        query += ' AND e.location LIKE ?'
        params.append(f'%{location}%')
    
    if include_enhanced:
        query += ' GROUP BY e.id'
    
    query += ' ORDER BY e.date, e.time'
    
    cursor.execute(query, params)
    events = cursor.fetchall()
    
    if not events:
        print("No events to export")
        logger.info("No events matched export criteria")
        conn.close()
        return 0
    
    # Define CSV headers based on what we're exporting
    if include_enhanced:
        fieldnames = [
            'ID', 'Title', 'Date', 'Time', 'Location', 'Description', 
            'Link', 'Event Type', 'SEO Score', 'Enhanced Description', 'Tags'
        ]
    else:
        fieldnames = [
            'ID', 'Title', 'Date', 'Time', 'Location', 'Description', 'Link'
        ]
    
    # Write to CSV
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(fieldnames)
        writer.writerows(events)
    
    conn.close()
    
    print(f"\n✓ Successfully exported {len(events)} events to {output_file}")
    logger.info(f"Exported {len(events)} events to CSV: {output_file}")
    
    return len(events)


@with_error_handling("iCal Export")
def export_to_ical(
    event_ids: Optional[List[int]] = None,
    output_file: str = "events.ics",
    event_type: Optional[str] = None,
    location: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> int:
    """
    Export events to iCal (.ics) format
    
    Args:
        event_ids: List of specific event IDs to export (None = all upcoming)
        output_file: Path to output .ics file
        event_type: Filter by event type
        location: Filter by location
        date_from: Filter events from date (YYYY-MM-DD)
        date_to: Filter events to date (YYYY-MM-DD)
    
    Returns:
        Number of events exported
    """
    if not ICAL_AVAILABLE:
        print("Error: icalendar library not installed")
        print("Install with: pip install icalendar")
        logger.error("Attempted iCal export without icalendar library")
        return 0
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Build query
    query = '''
        SELECT 
            e.id,
            e.title,
            e.date,
            e.time,
            e.location,
            e.description,
            e.link,
            ec.event_type
        FROM events e
        LEFT JOIN enhanced_content ec ON e.id = ec.event_id
        WHERE e.date >= DATE('now')
    '''
    
    params = []
    
    # Filter by specific event IDs
    if event_ids:
        placeholders = ','.join('?' * len(event_ids))
        query += f' AND e.id IN ({placeholders})'
        params.extend(event_ids)
    
    # Add other filters
    if date_from:
        query += ' AND e.date >= ?'
        params.append(date_from)
    if date_to:
        query += ' AND e.date <= ?'
        params.append(date_to)
    if event_type:
        query += ' AND ec.event_type LIKE ?'
        params.append(f'%{event_type}%')
    if location:
        query += ' AND e.location LIKE ?'
        params.append(f'%{location}%')
    
    query += ' ORDER BY e.date, e.time'
    
    cursor.execute(query, params)
    events = cursor.fetchall()
    
    if not events:
        print("No events to export")
        logger.info("No events matched iCal export criteria")
        conn.close()
        return 0
    
    # Create calendar
    cal = Calendar()
    cal.add('prodid', '-//Olympic College Event Manager//EN')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('method', 'PUBLISH')
    cal.add('x-wr-calname', 'Olympic College Events')
    cal.add('x-wr-caldesc', 'Events from Olympic College Event Manager')
    
    # Add events to calendar
    for event_id, title, date, time, loc, desc, link, event_type in events:
        event = ICalEvent()
        
        # Add basic info
        event.add('summary', title)
        event.add('uid', f'event-{event_id}@olympic.edu')
        
        # Parse date and time
        try:
            event_date = datetime.strptime(date, '%Y-%m-%d').date()
            
            if time:
                # Event with specific time
                event_time = datetime.strptime(time, '%H:%M').time()
                start_dt = datetime.combine(event_date, event_time)
                # Default to 1 hour duration
                end_dt = start_dt + timedelta(hours=1)
                
                event.add('dtstart', start_dt)
                event.add('dtend', end_dt)
            else:
                # All-day event
                event.add('dtstart', event_date)
                # For all-day events, end date is the next day
                event.add('dtend', event_date + timedelta(days=1))
                event.add('x-microsoft-cdo-alldayevent', 'TRUE')
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse date/time for event {event_id}: {e}")
            # Skip this event if date parsing fails
            continue
        
        # Add optional fields
        if desc:
            # Create description with event type if available
            full_desc = desc
            if event_type:
                full_desc = f"[{event_type}]\n\n{desc}"
            event.add('description', full_desc)
        
        if loc:
            event.add('location', loc)
        
        if link:
            event.add('url', link)
        
        # Add categories
        if event_type:
            event.add('categories', [event_type])
        
        # Add metadata
        event.add('dtstamp', datetime.now())
        event.add('created', datetime.now())
        event.add('last-modified', datetime.now())
        event.add('sequence', 0)
        event.add('status', 'CONFIRMED')
        event.add('transp', 'OPAQUE')
        
        cal.add_component(event)
    
    conn.close()
    
    # Write to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'wb') as f:
        f.write(cal.to_ical())
    
    print(f"\n✓ Successfully exported {len(events)} events to {output_file}")
    print(f"\nTo import into your calendar:")
    print(f"  • Google Calendar: Settings → Import & Export → Import")
    print(f"  • Outlook: File → Open & Export → Import/Export → Import an iCalendar (.ics)")
    print(f"  • Apple Calendar: File → Import")
    print(f"  • Or simply double-click the .ics file!")
    
    logger.info(f"Exported {len(events)} events to iCal: {output_file}")
    
    return len(events)


@with_error_handling("Single Event iCal Export")
def export_event_to_ical(event_id: int, output_file: Optional[str] = None) -> bool:
    """
    Export a single event to iCal format
    
    Args:
        event_id: Event ID to export
        output_file: Output filename (default: event_{id}.ics)
    
    Returns:
        True if successful, False otherwise
    """
    if output_file is None:
        output_file = f"event_{event_id}.ics"
    
    count = export_to_ical(event_ids=[event_id], output_file=output_file)
    return count > 0


def get_export_statistics():
    """Get statistics about available events for export"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total upcoming events
    cursor.execute('SELECT COUNT(*) FROM events WHERE date >= DATE("now")')
    total = cursor.fetchone()[0]
    
    # Events by type
    cursor.execute('''
        SELECT ec.event_type, COUNT(*)
        FROM events e
        LEFT JOIN enhanced_content ec ON e.id = ec.event_id
        WHERE e.date >= DATE("now") AND ec.event_type IS NOT NULL
        GROUP BY ec.event_type
        ORDER BY COUNT(*) DESC
    ''')
    by_type = cursor.fetchall()
    
    # Events by month
    cursor.execute('''
        SELECT strftime('%Y-%m', date) as month, COUNT(*)
        FROM events
        WHERE date >= DATE("now")
        GROUP BY month
        ORDER BY month
    ''')
    by_month = cursor.fetchall()
    
    conn.close()
    
    return {
        'total': total,
        'by_type': by_type,
        'by_month': by_month
    }


if __name__ == "__main__":
    # Example usage
    print("Event Export Module")
    print("=" * 60)
    
    stats = get_export_statistics()
    print(f"\nAvailable for export: {stats['total']} upcoming events")
    
    if stats['by_type']:
        print("\nEvents by type:")
        for event_type, count in stats['by_type']:
            print(f"  {event_type}: {count}")
    
    if stats['by_month']:
        print("\nEvents by month:")
        for month, count in stats['by_month']:
            print(f"  {month}: {count}")
