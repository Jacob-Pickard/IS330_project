import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import time
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from database.db_utils import get_db_connection

def cleanup_past_events():
    """Remove past events and duplicates from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get count of past events before deletion
        cursor.execute('SELECT COUNT(*) FROM events WHERE date < DATE("now")')
        past_events_count = cursor.fetchone()[0]
        
        # Delete past events
        cursor.execute('DELETE FROM events WHERE date < DATE("now")')
        
        # Get count of duplicates
        cursor.execute('''
            WITH duplicates AS (
                SELECT MIN(id) as keep_id, title, date, time
                FROM events 
                GROUP BY title, date, time
                HAVING COUNT(*) > 1
            )
            SELECT COUNT(*) FROM events e
            WHERE EXISTS (
                SELECT 1 FROM duplicates d
                WHERE e.title = d.title 
                AND e.date = d.date 
                AND COALESCE(e.time, '') = COALESCE(d.time, '')
                AND e.id != d.keep_id
            )
        ''')
        duplicate_count = cursor.fetchone()[0]
        
        # Remove duplicates, keeping the earliest entry
        cursor.execute('''
            DELETE FROM events
            WHERE id IN (
                SELECT e.id FROM events e
                INNER JOIN (
                    SELECT title, date, time, MIN(id) as keep_id
                    FROM events 
                    GROUP BY title, date, time
                    HAVING COUNT(*) > 1
                ) d ON e.title = d.title 
                    AND e.date = d.date 
                    AND COALESCE(e.time, '') = COALESCE(d.time, '')
                WHERE e.id != d.keep_id
            )
        ''')
        
        # Delete orphaned category associations
        cursor.execute('''
            DELETE FROM event_categories 
            WHERE event_id NOT IN (SELECT id FROM events)
        ''')
        
        conn.commit()
        print(f"\nCleanup summary:")
        print(f"- Removed {past_events_count} past events")
        print(f"- Removed {duplicate_count} duplicate events")
        
    except Exception as e:
        print(f"\nError cleaning up events: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

from datetime import datetime

def parse_datetime(datetime_str):
    """Parse the datetime string from the website into separate date and time."""
    if not datetime_str:
        return None, None
    
    try:
        # Handle cases where only date is provided (no time)
        if 'T' not in datetime_str:
            # Validate the date format
            datetime.strptime(datetime_str, '%Y-%m-%d')
            return datetime_str, None
            
        # Split datetime into date and time
        date_str, time_str = datetime_str.split('T')
        # Validate the date format
        datetime.strptime(date_str, '%Y-%m-%d')
        # Format time as HH:MM
        time_str = time_str[:5]
        return date_str, time_str
    except Exception as e:
        print(f"Error parsing datetime {datetime_str}: {e}")
        return None, None

def scrape_events():
    base_url = 'https://www.olympic.edu/events-calendar'
    current_page = 0
    events = []

    try:
        while True:
            url = f"{base_url}?page={current_page}"
            print(f"\nFetching events from: {url}")
            
            # Add a delay between requests to be polite
            time.sleep(1)
            
            response = requests.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            event_rows = soup.select('.views-row')
            
            if not event_rows:
                print("No more events found, stopping.")
                break

            for row in event_rows:
                try:
                    title_elem = row.select_one('.field-title a')
                    if not title_elem:
                        continue

                    title = title_elem.text.strip()
                    
                    # Get full description
                    description = row.select_one('.field-body')
                    description = description.text.strip() if description else None
                    
                    # Parse date and time
                    date_elem = row.select_one('.views-field-field-dates-value time')
                    datetime_str = date_elem.get('datetime') if date_elem else None
                    event_date, event_time = parse_datetime(datetime_str)
                    
                    # Skip events without a valid date or past events
                    if not event_date or datetime.strptime(event_date, '%Y-%m-%d') < datetime.now():
                        continue
                    
                    # Get location
                    location = row.select_one('.field-location')
                    location = location.text.strip() if location else None
                    
                    # Get link
                    link = title_elem.get('href')
                    if link:
                        link = f"https://www.olympic.edu{link}"

                    events.append({
                        'title': title,
                        'description': description,
                        'date': event_date,
                        'time': event_time,
                        'location': location,
                        'link': link
                    })

                    # Debug: Print each event as it's found
                    print(f"\nFound event:")
                    print(f"Title: {title}")
                    print(f"Date: {event_date}")
                    print(f"Time: {event_time}")
                    print(f"Location: {location}")
                    print(f"Link: {link}")
                    print(f"Description length: {len(description) if description else 0} chars")

                except Exception as e:
                    print(f"Error processing event: {e}")
                    continue

            if len(event_rows) < 10:  # Assuming pagination shows 10 events per page
                print("Reached last page, stopping.")
                break

            current_page += 1

        print(f"\nTotal events scraped: {len(events)}")
        return events

    except Exception as e:
        print(f"\nError scraping events: {str(e)}")
        return []

def save_events_to_db(events):
    if not events:
        print("No events to save.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        events_added = 0
        events_updated = 0
        
        for event in events:
            try:
                # Try to insert the event
                cursor.execute('''
                    INSERT INTO events (title, description, date, time, location, link)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    event['title'],
                    event['description'],
                    event['date'],
                    event['time'],
                    event['location'],
                    event['link']
                ))
                events_added += 1
            except sqlite3.IntegrityError:
                # If event already exists, update it
                cursor.execute('''
                    UPDATE events 
                    SET description = ?,
                        location = ?,
                        link = ?,
                        last_updated = DATETIME('now')
                    WHERE title = ? AND date = ? AND (time = ? OR (time IS NULL AND ? IS NULL))
                ''', (
                    event['description'],
                    event['location'],
                    event['link'],
                    event['title'],
                    event['date'],
                    event['time'],
                    event['time']
                ))
                events_updated += 1

        # Record the scraping in history
        cursor.execute('''
            INSERT INTO scraping_history 
            (start_time, end_time, events_scraped, status)
            VALUES (DATETIME('now'), DATETIME('now'), ?, 'success')
        ''', (events_added + events_updated,))

        conn.commit()
        print(f"\nDatabase update summary:")
        print(f"New events added: {events_added}")
        print(f"Existing events updated: {events_updated}")

    except Exception as e:
        print(f"\nError saving to database: {str(e)}")
        conn.rollback()

    finally:
        conn.close()

def view_events():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT title, date, time, location, description, link
            FROM events
            WHERE date >= DATE('now')
            ORDER BY date ASC, time ASC
            LIMIT 10
        ''')
        
        print("\nUpcoming events (next 10):")
        print("-" * 80)
        
        for event in cursor.fetchall():
            title, date, time, location, description, link = event
            print(f"Title: {title}")
            print(f"Date: {date}")
            if time:
                print(f"Time: {time}")
            if location:
                print(f"Location: {location}")
            if description:
                # Truncate description if it's too long
                desc = description if len(description) <= 200 else description[:197] + "..."
                print(f"Description: {desc}")
            print(f"Link: {link}")
            print("-" * 80)
            
    finally:
        conn.close()

def main():
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--view":
        view_events()
    else:
        print("Starting event scraping...")
        cleanup_past_events()  # Clean up before scraping new events
        events = scrape_events()
        if events:
            save_events_to_db(events)
        else:
            print("No events were scraped")

if __name__ == "__main__":
    main()