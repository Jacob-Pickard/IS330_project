import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))
from database.db_utils import get_db_connection as connect_db

def get_event_stats():
    """Gather comprehensive event statistics"""
    conn = connect_db()
    cursor = conn.cursor()
    
    stats = {}
    
    # Get total event count
    cursor.execute("SELECT COUNT(*) FROM events")
    stats['total_events'] = cursor.fetchone()[0]
    
    # Get events by building
    cursor.execute("""
        SELECT
            CASE 
                WHEN location LIKE '%Bldg%' THEN 
                    SUBSTR(location, INSTR(location, 'Bldg'), 
                          CASE 
                              WHEN INSTR(SUBSTR(location, INSTR(location, 'Bldg')), ',') = 0 
                              THEN LENGTH(SUBSTR(location, INSTR(location, 'Bldg')))
                              ELSE INSTR(SUBSTR(location, INSTR(location, 'Bldg')), ',') - 1
                          END)
                WHEN location LIKE '%Building%' THEN 
                    'Bldg ' || SUBSTR(location, INSTR(location, 'Building') + 9, 2)
                WHEN location LIKE 'Bldg. %' THEN
                    REPLACE(SUBSTR(location, 1, INSTR(location || ',', ',') - 1), 'Bldg. ', 'Bldg ')
                ELSE location 
            END as building,
            COUNT(*) as count
        FROM events
        WHERE location IS NOT NULL
            AND (
                location LIKE '%Bldg%'
                OR location LIKE '%Building%'
                OR location LIKE 'Bldg. %'
                OR (
                    location NOT LIKE '%.%'
                    AND location NOT LIKE '%/%'
                    AND location NOT LIKE '%(%'
                    AND location NOT LIKE '%)%'
                )
            )
        GROUP BY building
        ORDER BY count DESC
    """)
    stats['events_by_building'] = cursor.fetchall()
    
    # If no specific buildings found, try broader location analysis
    if len(stats['events_by_building']) == 0:
        cursor.execute("""
            SELECT 
                CASE
                    WHEN location LIKE '%Center%' THEN 'Various Centers'
                    WHEN location LIKE '%Room%' OR location LIKE '%Rm%' THEN 'Various Rooms'
                    WHEN location = 'Virtual' THEN 'Virtual Events'
                    WHEN location = 'Online' THEN 'Online Events'
                    ELSE location
                END as location_type,
                COUNT(*) as count
            FROM events
            WHERE location IS NOT NULL
            AND location != ''
            GROUP BY location_type
            ORDER BY count DESC
            LIMIT 5
        """)
        stats['events_by_building'] = cursor.fetchall()
    
    # Get event type distribution
    cursor.execute("""
        SELECT event_type, COUNT(*) as count
        FROM enhanced_content
        WHERE event_type IS NOT NULL
        GROUP BY event_type
        ORDER BY count DESC
    """)
    stats['event_types'] = cursor.fetchall()
    
    # Get average SEO scores
    cursor.execute("""
        SELECT 
            AVG(seo_score) as avg_score,
            MIN(seo_score) as min_score,
            MAX(seo_score) as max_score
        FROM enhanced_content
        WHERE seo_score IS NOT NULL
    """)
    stats['seo_stats'] = cursor.fetchone()
    
    return stats

def run_enhanced_analysis():
    """Run enhanced analysis on event data"""
    stats = get_event_stats()
    
    building_usage = {}
    for building, count in stats['events_by_building']:
        # Calculate utilization percentage relative to highest usage building
        max_count = max(c for _, c in stats['events_by_building'])
        utilization = (count / max_count) * 100
        
        # Determine peak times based on high SEO scores
        peak_times = []
        if count >= max_count * 0.7:  # If usage is at least 70% of max
            peak_times.append("Morning")
        if count >= max_count * 0.8:  # If usage is at least 80% of max
            peak_times.append("Afternoon")
        if not peak_times:  # If no peaks determined, add standard time
            peak_times.append("Variable")
        
        building_usage[building] = {
            'count': count,
            'peak_times': peak_times,
            'utilization': round(utilization, 1)
        }
    
    # Generate recurring patterns insights
    recurring_patterns = []
    if stats['event_types']:
        top_types = sorted(stats['event_types'], key=lambda x: x[1], reverse=True)[:3]
        for event_type, count in top_types:
            if count > 1:
                recurring_patterns.append(f"{event_type} events occur most frequently ({count} events)")
    
    # Generate AI insights based on the data patterns
    ai_insights = []
    
    # Building usage insights
    most_used = max(stats['events_by_building'], key=lambda x: x[1])
    ai_insights.append(f"{most_used[0]} is the most utilized building with {most_used[1]} events")
    
    # Type distribution insights
    if stats['event_types']:
        top_type = max(stats['event_types'], key=lambda x: x[1])
        ai_insights.append(f"Most common event type is {top_type[0]} with {top_type[1]} events")
    
    # SEO insights
    if stats['seo_stats']:
        avg, min_score, max_score = stats['seo_stats']
        ai_insights.append(f"Average SEO score is {avg:.1f}, ranging from {min_score:.1f} to {max_score:.1f}")
    
    return {
        'building_usage': building_usage,
        'recurring_patterns': recurring_patterns,
        'ai_insights': ai_insights
    }
    print()
    
    # Display event types
    print("Event Type Distribution:")
    print("----------------------")
    for type_, count in stats['event_types']:
        print(f"{type_}: {count} events")
    print()
    
    # Generate and display AI insights
    print("AI-Generated Insights:")
    print("--------------------")
    insights = generate_insights(stats)
    print(insights)

if __name__ == "__main__":
    run_enhanced_analysis()