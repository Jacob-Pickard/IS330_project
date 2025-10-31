import sqlite3
import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from database.db_utils import get_db_connection
from content_enhancement.content_enhancer import ContentEnhancer

def enhance_database():
    """Add enhanced content tables and update existing events"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create enhanced content table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS enhanced_content (
        event_id INTEGER PRIMARY KEY,
        enhanced_description TEXT,
        structured_time TEXT,
        structured_location TEXT,
        event_type TEXT,
        seo_score INTEGER,
        missing_details TEXT,
        FOREIGN KEY (event_id) REFERENCES events (id) ON DELETE CASCADE
    )
    ''')

    # Create tags table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS event_tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        tag TEXT NOT NULL,
        FOREIGN KEY (event_id) REFERENCES events (id) ON DELETE CASCADE
    )
    ''')

    # Create unique index for event_tags
    cursor.execute('''
    CREATE UNIQUE INDEX IF NOT EXISTS idx_event_tags 
    ON event_tags(event_id, tag)
    ''')

    # Add triggers for automatic content enhancement
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS enhance_event_content_insert
    AFTER INSERT ON events
    BEGIN
        INSERT INTO enhanced_content (
            event_id,
            enhanced_description,
            structured_time,
            structured_location,
            event_type,
            seo_score,
            missing_details
        ) VALUES (
            NEW.id,
            NULL, NULL, NULL, NULL, 0, NULL
        );
    END;
    ''')

    conn.commit()
    
    # Enhance existing events
    enhance_existing_events()

def enhance_existing_events():
    """Enhance all existing events in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    enhancer = ContentEnhancer()

    # Get all events that need enhancement
    cursor.execute('''
    SELECT e.id, e.title, e.description 
    FROM events e
    LEFT JOIN enhanced_content ec ON e.id = ec.event_id
    WHERE ec.event_id IS NULL OR ec.enhanced_description IS NULL
    ''')
    
    events = cursor.fetchall()
    
    for event_id, title, description in events:
        if not description:
            description = ""
            
        # Generate enhancements
        enhanced_desc = enhancer.enhance_description(title, description)
        tags = enhancer.generate_tags(title, description)
        seo_suggestions = enhancer.suggest_seo_improvements(title, description)
        
        # Calculate SEO score (0-100)
        seo_score = calculate_seo_score(title, description, seo_suggestions)
        
        # Extract structured information
        time_info = enhancer._extract_time_info(description)
        location_info = enhancer._extract_location_info(description)
        event_type = enhancer._identify_event_type(title + " " + description)
        
        # Store missing details as JSON string
        missing_details = ', '.join(seo_suggestions.get('description_suggestions', []))
        
        # Update enhanced content
        cursor.execute('''
        INSERT OR REPLACE INTO enhanced_content (
            event_id,
            enhanced_description,
            structured_time,
            structured_location,
            event_type,
            seo_score,
            missing_details
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            event_id,
            enhanced_desc,
            time_info,
            location_info,
            event_type,
            seo_score,
            missing_details
        ))
        
        # Update tags
        cursor.execute('DELETE FROM event_tags WHERE event_id = ?', (event_id,))
        for tag in tags:
            cursor.execute('''
            INSERT OR IGNORE INTO event_tags (event_id, tag)
            VALUES (?, ?)
            ''', (event_id, tag))
    
    conn.commit()

def calculate_seo_score(title: str, description: str, seo_suggestions: dict) -> int:
    """Calculate an SEO score based on content quality"""
    score = 100
    
    # Deduct points for missing elements
    if not title:
        score -= 30
    elif len(title) < 5:
        score -= 20
    elif len(title) > 70:
        score -= 10
        
    if not description:
        score -= 30
    elif len(description) < 100:
        score -= 15
        
    # Deduct points for each missing element
    score -= len(seo_suggestions.get('title_suggestions', [])) * 5
    score -= len(seo_suggestions.get('description_suggestions', [])) * 5
    
    return max(0, min(100, score))

def get_enhanced_event(event_id: int) -> dict:
    """Get an event with all its enhanced content"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT 
        e.title,
        e.description,
        e.date,
        e.time,
        e.location,
        ec.enhanced_description,
        ec.structured_time,
        ec.structured_location,
        ec.event_type,
        ec.seo_score,
        ec.missing_details,
        GROUP_CONCAT(et.tag) as tags
    FROM events e
    LEFT JOIN enhanced_content ec ON e.id = ec.event_id
    LEFT JOIN event_tags et ON e.id = et.event_id
    WHERE e.id = ?
    GROUP BY e.id
    ''', (event_id,))
    
    row = cursor.fetchone()
    if not row:
        return None
        
    return {
        'title': row[0],
        'description': row[1],
        'date': row[2],
        'time': row[3],
        'location': row[4],
        'enhanced_description': row[5],
        'structured_time': row[6],
        'structured_location': row[7],
        'event_type': row[8],
        'seo_score': row[9],
        'missing_details': row[10].split(', ') if row[10] else [],
        'tags': row[11].split(',') if row[11] else []
    }

def main():
    """Main function to enhance database content"""
    enhance_database()
    
    # Test enhancement with a sample event
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Add a sample event if none exist
    cursor.execute('SELECT COUNT(*) FROM events')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
        INSERT INTO events (title, description, date, time, location)
        VALUES (
            'Student Leadership Workshop',
            'Join us on November 15th at 2:30 PM in the Student Center Room 105 for an interactive workshop on leadership skills. Learn about team management, communication, and project planning.',
            '2025-11-15',
            '14:30',
            'Student Center Room 105'
        )
        ''')
        conn.commit()
        
        # Get the inserted event's ID
        cursor.execute('SELECT last_insert_rowid()')
        event_id = cursor.fetchone()[0]
        
        # Enhance the event
        enhance_existing_events()
        
        # Display the enhanced event
        event = get_enhanced_event(event_id)
        if event:
            print("\nEnhanced Event Content:")
            for key, value in event.items():
                print(f"\n{key.replace('_', ' ').title()}:")
                print(value)

if __name__ == "__main__":
    main()