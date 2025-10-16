import os
from pathlib import Path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from database.db_utils import get_db_connection, get_db_path

def init_database():
    # Create database directory if it doesn't exist
    db_dir = os.path.dirname(get_db_path())
    os.makedirs(db_dir, exist_ok=True)
    
    # Connect to SQLite database (creates it if it doesn't exist)
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create events table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        date DATE,
        time TIME,
        location TEXT,
        link TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(link)
    )
    ''')

    # Create categories table for event categorization
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT
    )
    ''')

    # Create event_categories junction table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS event_categories (
        event_id INTEGER,
        category_id INTEGER,
        FOREIGN KEY (event_id) REFERENCES events (id),
        FOREIGN KEY (category_id) REFERENCES categories (id),
        PRIMARY KEY (event_id, category_id)
    )
    ''')

    # Create a table for tracking scraping history
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS scraping_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        start_time DATETIME NOT NULL,
        end_time DATETIME,
        events_scraped INTEGER,
        status TEXT,
        error_message TEXT
    )
    ''')

    # Insert sample categories
    sample_categories = [
        ('Academic', 'Academic events and deadlines'),
        ('Sports', 'Athletic events and competitions'),
        ('Arts', 'Art exhibitions and performances'),
        ('Student Life', 'Student activities and social events'),
        ('Career', 'Career fairs and job opportunities')
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO categories (name, description)
        VALUES (?, ?)
    ''', sample_categories)

    # Insert sample events
    sample_events = [
        (
            'Fall Quarter Registration Deadline',
            'Last day to register for Fall Quarter classes. Registration must be completed online or in-person by 5:00 PM.',
            '2025-09-30 17:00:00',
            'Online/Student Services Building',
            'https://www.olympic.edu/registration'
        ),
        (
            'Basketball Game: Rangers vs Peninsula Pirates',
            'Come support our Olympic College Rangers as they face off against Peninsula College!',
            '2025-10-15 19:00:00',
            'Bremer Student Center Gym',
            'https://www.olympic.edu/athletics/basketball'
        ),
        (
            'Student Art Exhibition Opening',
            'Featuring works from current OC art students. Light refreshments will be served.',
            '2025-10-05 18:00:00',
            'Art Building Gallery',
            'https://www.olympic.edu/arts/gallery'
        ),
        (
            'Fall Career Fair',
            'Meet with local employers and explore job opportunities. Bring your resume!',
            '2025-11-01 10:00:00',
            'William D. Harvey Theater',
            'https://www.olympic.edu/career-fair'
        )
    ]

    cursor.executemany('''
        INSERT OR IGNORE INTO events (title, description, date, location, link)
        VALUES (?, ?, ?, ?, ?)
    ''', sample_events)

    # Link events to categories
    event_categories = [
        (1, 1),  # Registration Deadline -> Academic
        (2, 2),  # Basketball Game -> Sports
        (3, 3),  # Art Exhibition -> Arts
        (4, 5)   # Career Fair -> Career
    ]

    cursor.executemany('''
        INSERT OR IGNORE INTO event_categories (event_id, category_id)
        VALUES (?, ?)
    ''', event_categories)

    # Add a sample scraping history entry
    cursor.execute('''
        INSERT INTO scraping_history (start_time, end_time, events_scraped, status)
        VALUES (DATETIME('now', '-1 hour'), DATETIME('now'), 4, 'success')
    ''')

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print(f"Database initialized successfully with sample data at: {get_db_path()}")

if __name__ == "__main__":
    init_database()