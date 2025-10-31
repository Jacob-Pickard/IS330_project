import sys
from pathlib import Path
from collections import Counter
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))
from database.db_utils import get_db_connection as connect_db

def analyze_events():
    conn = connect_db()
    cursor = conn.cursor()
    analysis = {}
    
    # 1. Most common event locations
    cursor.execute("""
        SELECT location, COUNT(*) as count 
        FROM events 
        WHERE location IS NOT NULL 
        GROUP BY location 
        ORDER BY count DESC 
        LIMIT 5
    """)
    analysis['top_locations'] = {loc: count for loc, count in cursor.fetchall()}

    # 2. Events by day of week
    cursor.execute("""
        SELECT 
            CASE CAST(strftime('%w', date) AS INTEGER)
            WHEN 0 THEN 'Sunday'
            WHEN 1 THEN 'Monday'
            WHEN 2 THEN 'Tuesday'
            WHEN 3 THEN 'Wednesday'
            WHEN 4 THEN 'Thursday'
            WHEN 5 THEN 'Friday'
            WHEN 6 THEN 'Saturday'
        END as day_of_week,
        COUNT(*) as count
        FROM events
        GROUP BY day_of_week
        ORDER BY CAST(strftime('%w', date) AS INTEGER)
    """)
    analysis['day_distribution'] = {day: count for day, count in cursor.fetchall()}

    # 3. Events per month
    cursor.execute("""
        SELECT 
            strftime('%m', date) as month,
            COUNT(*) as count
        FROM events
        WHERE date LIKE '2025%'
        GROUP BY month
        ORDER BY month
    """)
    months = ['January', 'February', 'March', 'April', 'May', 'June', 
              'July', 'August', 'September', 'October', 'November', 'December']
    month_results = cursor.fetchall()
    analysis['month_distribution'] = {
        months[int(month_num) - 1]: count 
        for month_num, count in month_results
    }

    # 4. Events with/without specific time
    cursor.execute("""
        SELECT 
            CASE WHEN time IS NULL THEN 'No specific time' 
            ELSE 'Has specific time' END as time_status,
            COUNT(*) as count
        FROM events
        GROUP BY time_status
    """)
    analysis['time_specifications'] = {status: count for status, count in cursor.fetchall()}

    conn.close()
    return analysis

if __name__ == "__main__":
    # If run directly, print the analysis results
    analysis = analyze_events()
    
    print("\nTop 5 Most Common Event Locations:")
    for location, count in analysis['top_locations'].items():
        print(f"- {location}: {count} events")
    
    print("\nEvents by Day of Week:")
    for day, count in analysis['day_distribution'].items():
        print(f"- {day}: {count} events")
    
    print("\nNumber of Events by Month (2025):")
    for month, count in analysis['month_distribution'].items():
        print(f"- {month}: {count} events")
    
    print("\nTime Specification Analysis:")
    for status, count in analysis['time_specifications'].items():
        print(f"- {status}: {count} events")