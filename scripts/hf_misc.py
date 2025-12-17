from datetime import timedelta
import os
import re
import sqlite3

def get_db_connection(db_name='database.db'):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    db_path = os.path.join(project_root, 'databases', db_name)
    print(f"Opening database at: {db_path}") 
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def parse_duration(duration):
    time_units = {
        'w': 7 * 24 * 60 * 60,
        'd': 24 * 60 * 60,
        'h': 60 * 60,
        'm': 60,
        's': 1,
    }
    pattern = r'(\d+)\s*(w|d|h|m|s)'
    matches = re.findall(pattern, duration.lower())
    
    if not matches:
        raise ValueError("Invalid duration format")
    
    total_seconds = sum(int(value) * time_units[unit] for value, unit in matches)
    return timedelta(seconds=total_seconds)