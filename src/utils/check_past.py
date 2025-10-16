import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from database.db_utils import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

cursor.execute('SELECT title, date, time FROM events WHERE date < "2025-11-05"')
print('Past events:')
for title, date, time in cursor.fetchall():
    print(f'{title} on {date} at {time}')

conn.close()