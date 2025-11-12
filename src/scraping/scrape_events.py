import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import time
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from database.db_utils import get_db_connection
from database.validation import EventValidator, DuplicateDetector, validate_batch_events
from database.error_handling import (
    with_error_handling,
    DatabaseTransaction,
    ScrapingErrorHandler,
    RecoveryManager,
    logger,
    log_operation_stats,
    ScrapingError,
    ValidationError
)

@with_error_handling("Cleanup past events")
def cleanup_past_events():
    """Remove past events and duplicates from the database."""
    conn = get_db_connection()
    
    try:
        with DatabaseTransaction(conn, "Cleanup past events") as cursor:
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
            
            print(f"\nCleanup summary:")
            print(f"- Removed {past_events_count} past events")
            print(f"- Removed {duplicate_count} duplicate events")
            
            logger.info(f"Cleanup completed: {past_events_count} past events, {duplicate_count} duplicates removed")
        
    except Exception as e:
        logger.error(f"Error cleaning up events: {str(e)}")
        print(f"\nError cleaning up events: {str(e)}")
        raise
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

@with_error_handling("Scrape events")
def scrape_events():
    base_url = 'https://www.olympic.edu/events-calendar'
    current_page = 0
    events = []
    error_handler = ScrapingErrorHandler(max_retries=3, retry_delay=5)

    def scrape_page(url):
        """Scrape a single page of events"""
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')

    try:
        while True:
            url = f"{base_url}?page={current_page}"
            print(f"\nFetching events from: {url}")
            
            # Add a delay between requests to be polite
            time.sleep(1)
            
            # Use error handler with retry logic
            soup = error_handler.scrape_with_retry(scrape_page, url)
            
            if soup is None:
                logger.warning(f"Failed to scrape page {current_page}, stopping")
                break
            
            event_rows = soup.select('.views-row')
            
            if not event_rows:
                print("No more events found, stopping.")
                logger.info(f"Scraping complete: {len(events)} events found")
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
                    logger.warning(f"Error processing event: {e}")
                    print(f"Error processing event: {e}")
                    continue

            if len(event_rows) < 10:  # Assuming pagination shows 10 events per page
                print("Reached last page, stopping.")
                break

            current_page += 1

        # Save failed URLs if any
        if error_handler.get_failed_urls():
            error_handler.save_failed_urls()

        print(f"\nTotal events scraped: {len(events)}")
        log_operation_stats("Scraping", {
            "Total events": len(events),
            "Pages scraped": current_page + 1,
            "Failed URLs": len(error_handler.get_failed_urls())
        })
        
        return events

    except Exception as e:
        logger.error(f"Critical error scraping events: {str(e)}")
        print(f"\nError scraping events: {str(e)}")
        raise ScrapingError(f"Failed to scrape events: {str(e)}")

@with_error_handling("Save events to database")
def save_events_to_db(events):
    if not events:
        print("No events to save.")
        logger.info("No events to save")
        return

    conn = get_db_connection()
    recovery_mgr = RecoveryManager(conn)
    
    # Create backup before major changes
    logger.info("Creating database backup before saving events")
    backup_path = recovery_mgr.create_backup()
    print(f"Database backup created: {backup_path.name}")
    
    try:
        # Validate events before saving
        print("\nValidating events...")
        logger.info(f"Validating {len(events)} events")
        
        valid_events, invalid_events, stats = validate_batch_events(events)
        
        if invalid_events:
            print(f"\nValidation warnings: {len(invalid_events)} events have issues")
            logger.warning(f"{len(invalid_events)} events failed validation")
            
            for invalid in invalid_events[:5]:  # Show first 5
                print(f"- {invalid['data'].get('title', 'Unknown')}: {', '.join(invalid['errors'])}")
                logger.debug(f"Validation error: {invalid['data'].get('title')} - {invalid['errors']}")
        
        if not valid_events:
            print("\nNo valid events to save!")
            logger.error("All events failed validation")
            raise ValidationError("No valid events to save")
        
        print(f"\n{len(valid_events)} events passed validation")
        logger.info(f"{len(valid_events)} events passed validation")
        
        # Check for duplicates
        duplicate_detector = DuplicateDetector(conn)
        
        events_added = 0
        events_updated = 0
        events_skipped = 0
        
        with DatabaseTransaction(conn, "Save events to database") as cursor:
            for event in valid_events:
                try:
                    # Check if this is a duplicate of an existing event
                    is_dup, dup_id, reason = duplicate_detector.is_duplicate(event)
                    if is_dup:
                        logger.debug(f"Skipping duplicate event: {event['title']} ({reason})")
                        events_skipped += 1
                        continue
                    
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
                    logger.debug(f"Added new event: {event['title']}")
                    
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
                    logger.debug(f"Updated existing event: {event['title']}")

            # Record the scraping in history
            cursor.execute('''
                INSERT INTO scraping_history 
                (start_time, end_time, events_scraped, status)
                VALUES (DATETIME('now'), DATETIME('now'), ?, 'success')
            ''', (events_added + events_updated,))

        print(f"\nDatabase update summary:")
        print(f"New events added: {events_added}")
        print(f"Existing events updated: {events_updated}")
        print(f"Duplicate events skipped: {events_skipped}")
        print(f"Invalid events: {len(invalid_events)}")
        
        log_operation_stats("Database Save", {
            "Valid events": len(valid_events),
            "Invalid events": len(invalid_events),
            "Events added": events_added,
            "Events updated": events_updated,
            "Duplicates skipped": events_skipped
        })
        
        # Verify database integrity after save
        is_valid, errors = recovery_mgr.verify_database_integrity()
        if not is_valid:
            logger.error(f"Database integrity check failed: {errors}")
            print(f"\nWarning: Database integrity issues detected: {errors}")
        
        # Generate recommendations for all events
        print("\nGenerating event recommendations...")
        logger.info("Generating event recommendations")
        try:
            from analysis.recommendations import generate_all_recommendations
            rec_stats = generate_all_recommendations()
            logger.info(f"Recommendations generated: {rec_stats}")
        except Exception as e:
            logger.warning(f"Failed to generate recommendations: {str(e)}")
            print(f"Warning: Could not generate recommendations: {str(e)}")

    except Exception as e:
        logger.error(f"Error saving to database: {str(e)}")
        print(f"\nError saving to database: {str(e)}")
        print("Database changes have been rolled back")
        raise

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