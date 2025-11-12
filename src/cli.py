#!/usr/bin/env python
import sys
from pathlib import Path
import argparse
from datetime import datetime

sys.path.append(str(Path(__file__).parent))
from database.enhance_db import get_enhanced_event, main as enhance_db
from database.db_utils import get_db_connection
from database.init_db import init_database
from scraping.scrape_events import scrape_events
from analysis.basic_analysis import analyze_events
from analysis.enhanced_analysis import run_enhanced_analysis
from analysis.conflict_detection import run_conflict_detection
from analysis.recommendations import generate_all_recommendations, display_event_with_recommendations, get_event_recommendations
from utils.export_events import export_to_csv, export_to_ical, export_event_to_ical, get_export_statistics

def list_upcoming_events(limit=10, event_type=None, location=None, date_from=None, date_to=None):
    """List upcoming events with their IDs"""
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Build query with filters
    query = '''
        SELECT e.id, e.title, e.date, ec.event_type, ec.seo_score 
        FROM events e 
        LEFT JOIN enhanced_content ec ON e.id = ec.event_id 
        WHERE e.date >= ?
    '''
    params = [today if not date_from else date_from]
    
    if date_to:
        query += ' AND e.date <= ?'
        params.append(date_to)
    if event_type:
        query += ' AND ec.event_type LIKE ?'
        params.append(f'%{event_type}%')
    if location:
        query += ' AND e.location LIKE ?'
        params.append(f'%{location}%')
        
    query += ' ORDER BY e.date'
    if limit:
        query += ' LIMIT ?'
        params.append(limit)
    
    cursor.execute(query, params)
    events = cursor.fetchall()
    
    print("\nUpcoming Events:")
    print("="*80)
    print(f"{'ID':>5} | {'Date':<12} | {'Type':<15} | {'SEO':>4} | Title")
    print("-"*80)
    
    for event_id, title, date, event_type, seo_score in events:
        print(f"{event_id:>5} | {str(date):<12} | {str(event_type)[:15]:<15} | {seo_score or 0:>4} | {title}")

def show_event_details(event_id):
    """Show detailed enhancement analysis for a specific event"""
    event = get_enhanced_event(event_id)
    if not event:
        print(f"\nError: No event found with ID {event_id}")
        return
        
    print("\nEvent Enhancement Analysis")
    print("="*80)
    print(f"Title: {event['title']}")
    print(f"Date: {event['date']}")
    print(f"Time: {event['time']}")
    print(f"Location: {event['location']}")
    print(f"Event Type: {event['event_type']}")
    print(f"SEO Score: {event['seo_score']}/100")
    
    print("\nEnhanced Description:")
    print("-"*80)
    print(event['enhanced_description'])
    
    print("\nImprovement Suggestions:")
    print("-"*80)
    for suggestion in event['missing_details']:
        print(f"- {suggestion}")
    
    print("\nAuto-generated Tags:")
    print("-"*80)
    if event['tags']:
        print(', '.join(event['tags']))
    else:
        print("No tags generated")
    
    # Show recommendations
    recommendations = get_event_recommendations(event_id)
    if recommendations:
        print(f"\n{'─'*80}")
        print("SCHEDULING RECOMMENDATIONS")
        print(f"{'─'*80}")
        
        if recommendations['has_conflicts']:
            severity_symbols = {
                'high': '🔴 HIGH',
                'medium': '🟡 MEDIUM',
                'low': '🟢 LOW',
                'none': '⚪ NONE'
            }
            severity_display = severity_symbols.get(recommendations['severity'], recommendations['severity'])
            
            print(f"Severity: {severity_display}")
            print(f"Conflict Type: {recommendations['conflict_type'].replace('_', ' ').title()}")
            
            if recommendations['recommended_action']:
                print(f"\nRecommended Action:")
                print(f"  → {recommendations['recommended_action']}")
            
            if recommendations['alternative_times']:
                print(f"\nAlternative Time Slots:")
                for i, time_slot in enumerate(recommendations['alternative_times'], 1):
                    print(f"  {i}. {time_slot}")
            
            if recommendations['details']:
                print(f"\nDetails:")
                print(f"  {recommendations['details']}")
        else:
            print("✓ No conflicts detected - event is optimally scheduled")
        
        print(f"\nLast updated: {recommendations['generated_at']}")
    
    print("="*80)

def show_basic_analysis():
    """Show basic statistical analysis"""
    print("\nRunning Basic Statistical Analysis...")
    print("="*80)
    analysis = analyze_events()
    
    print("\nEvent Distribution:")
    print("-"*40)
    for day, count in analysis['day_distribution'].items():
        print(f"{day:12}: {count:3} events")
        
    print("\nTop Locations:")
    print("-"*40)
    for location, count in analysis['top_locations'].items():
        print(f"{location:30}: {count:3} events")
        
    print("\nTime Specifications:")
    print("-"*40)
    time_stats = analysis['time_specifications']
    total = sum(time_stats.values())
    for spec, count in time_stats.items():
        percentage = (count/total) * 100 if total > 0 else 0
        print(f"{spec:15}: {count:3} events ({percentage:.1f}%)")

def show_enhanced_analysis():
    """Show AI-powered enhanced analysis"""
    print("\nRunning Enhanced AI Analysis...")
    print("="*80)
    analysis = run_enhanced_analysis()
    
    print("\nBuilding Usage Patterns:")
    print("-"*40)
    for building, stats in analysis['building_usage'].items():
        print(f"\n{building}:")
        print(f"  Events: {stats['count']}")
        print(f"  Peak times: {', '.join(stats['peak_times'])}")
        print(f"  Utilization: {stats['utilization']}%")
    
    print("\nRecurring Event Patterns:")
    print("-"*40)
    for pattern in analysis['recurring_patterns']:
        print(f"- {pattern}")
    
    print("\nAI Insights:")
    print("-"*40)
    for insight in analysis['ai_insights']:
        print(f"- {insight}")

def main():
    parser = argparse.ArgumentParser(
        description='Olympic College Event Manager CLI',
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Event viewing and analysis
    view_group = parser.add_argument_group('View and Analysis')
    view_group.add_argument('--list', action='store_true', 
                           help='List upcoming events')
    view_group.add_argument('--list-all', action='store_true',
                           help='List all events')
    view_group.add_argument('--event', type=int, 
                           help='Show details for a specific event ID')
    view_group.add_argument('--basic-analysis', action='store_true',
                           help='Show basic statistical analysis')
    view_group.add_argument('--enhanced-analysis', action='store_true',
                           help='Show AI-powered enhanced analysis')
    view_group.add_argument('--detect-conflicts', action='store_true',
                           help='Detect scheduling conflicts and double-bookings')
    view_group.add_argument('--generate-recommendations', action='store_true',
                           help='Generate scheduling recommendations for all events')
    
    # Export commands
    export_group = parser.add_argument_group('Export')
    export_group.add_argument('--export-csv', 
                             help='Export events to CSV file (specify filename)')
    export_group.add_argument('--export-ical', 
                             help='Export events to iCal file (specify filename)')
    export_group.add_argument('--export-event-ical', type=int,
                             help='Export single event to iCal (specify event ID)')
    export_group.add_argument('--include-enhanced', action='store_true',
                             help='Include enhanced content in CSV export')
    
    # Data management
    data_group = parser.add_argument_group('Data Management')
    data_group.add_argument('--init-db', action='store_true',
                           help='Initialize or reset the database')
    data_group.add_argument('--scrape', action='store_true',
                           help='Scrape new events from the website')
    data_group.add_argument('--enhance-all', action='store_true',
                           help='Enhance all events in database')
    
    # Filtering and sorting
    filter_group = parser.add_argument_group('Filtering and Sorting')
    filter_group.add_argument('--type', 
                            help='Filter events by type (e.g., Academic, Arts)')
    filter_group.add_argument('--location',
                            help='Filter events by location')
    filter_group.add_argument('--date-from',
                            help='Filter events from date (YYYY-MM-DD)')
    filter_group.add_argument('--date-to',
                            help='Filter events to date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    # Handle database initialization
    if args.init_db:
        print("\nInitializing database...")
        init_database()
        print("Database initialized successfully!")
        return
        
    # Handle scraping
    if args.scrape:
        print("\nScraping events...")
        scrape_events()
        print("Event scraping completed!")
        
        # Automatically run conflict detection after scraping
        print("\nRunning automatic conflict detection...")
        conflicts = run_conflict_detection()
        
        # Show summary
        if conflicts and conflicts.get('summary', {}).get('total', 0) > 0:
            print("\n⚠️  WARNING: Scheduling conflicts detected!")
            print("Review the conflict report above for details.")
        
        return
        
    # Handle enhancement
    if args.enhance_all:
        print("\nEnhancing all events...")
        enhance_db()
        print("Enhancement complete!")
        return
        
    # Handle viewing and analysis
    if args.list or args.list_all:
        limit = None if args.list_all else 10
        list_upcoming_events(
            limit=limit,
            event_type=args.type,
            location=args.location,
            date_from=args.date_from,
            date_to=args.date_to
        )
        return
        
    if args.event:
        show_event_details(args.event)
        return
        
    if args.basic_analysis:
        show_basic_analysis()
        return
        
    if args.enhanced_analysis:
        show_enhanced_analysis()
        return
    
    if args.detect_conflicts:
        run_conflict_detection()
        return
    
    if args.generate_recommendations:
        print("\nGenerating event recommendations...")
        stats = generate_all_recommendations()
        return
    
    # Export commands
    if args.export_csv:
        export_to_csv(
            output_file=args.export_csv,
            event_type=args.type,
            location=args.location,
            date_from=args.date_from,
            date_to=args.date_to,
            include_enhanced=args.include_enhanced
        )
        return
    
    if args.export_ical:
        export_to_ical(
            event_ids=None,  # Export all matching events
            output_file=args.export_ical,
            event_type=args.type,
            location=args.location,
            date_from=args.date_from,
            date_to=args.date_to
        )
        return
    
    if args.export_event_ical:
        export_event_to_ical(
            event_id=args.export_event_ical
        )
        return
        
    # If no arguments provided, show usage
    if len(sys.argv) == 1:
        parser.print_help()

if __name__ == "__main__":
    main()