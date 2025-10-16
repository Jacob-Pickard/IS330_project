import sys
from pathlib import Path
from collections import Counter
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))
from database.db_utils import get_db_connection as connect_db

def analyze_events():
    conn = connect_db()
    cursor = conn.cursor()
    
    # 1. Most common event locations
    print("Top 5 Most Common Event Locations:")
    cursor.execute("""
        SELECT location, COUNT(*) as count 
        FROM events 
        WHERE location IS NOT NULL 
        GROUP BY location 
        ORDER BY count DESC 
        LIMIT 5
    """)
    for location, count in cursor.fetchall():
        print(f"- {location}: {count} events")
    print()

    # 2. Events by day of week
    print("Events by Day of Week:")
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
    for day, count in cursor.fetchall():
        print(f"- {day}: {count} events")
    print()

    # 3. Events per month
    print("Number of Events by Month (2025):")
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
    for month_num, count in cursor.fetchall():
        month_name = months[int(month_num) - 1]
        print(f"- {month_name}: {count} events")
    print()

    # 4. Events with/without specific time
    cursor.execute("""
        SELECT 
            CASE WHEN time IS NULL THEN 'No specific time' 
            ELSE 'Has specific time' END as time_status,
            COUNT(*) as count
        FROM events
        GROUP BY time_status
    """)
    print("Time Specification Analysis:")
    for status, count in cursor.fetchall():
        print(f"- {status}: {count} events")

    conn.close()

if __name__ == "__main__":
    analyze_events()