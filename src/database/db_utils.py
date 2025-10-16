import sqlite3
import os
from pathlib import Path

def get_db_path():
    """Get the absolute path to the database file."""
    return os.path.join(Path(__file__).parent.parent.parent, 'data', 'olympic_college.db')

def get_db_connection():
    """Create and return a database connection."""
    return sqlite3.connect(get_db_path())

def execute_query(query, params=None, fetch=True):
    """Execute a query and optionally fetch results."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        if fetch:
            result = cursor.fetchall()
        else:
            result = None
            conn.commit()
            
        return result
    finally:
        conn.close()

def execute_many(query, params):
    """Execute many queries at once."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.executemany(query, params)
        conn.commit()
    finally:
        conn.close()