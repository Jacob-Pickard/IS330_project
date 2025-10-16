from datetime import datetime
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from database.db_utils import get_db_connection

def check_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    print('Past Events Check:')
    cursor.execute('SELECT COUNT(*) FROM events WHERE date < date("now")')
    print(f'Number of past events: {cursor.fetchone()[0]}')

    print('\nDuplicate Check:')
    cursor.execute('''
        SELECT title, date, COUNT(*) as cnt 
        FROM events 
        GROUP BY title, date 
        HAVING cnt > 1
    ''')
    print('Duplicate events (if any):')
    duplicates = cursor.fetchall()
    if duplicates:
        for row in duplicates:
            print(f'Title: {row[0]}, Date: {row[1]}, Count: {row[2]}')
    else:
        print('No duplicates found')

    conn.close()

if __name__ == "__main__":
    check_database()