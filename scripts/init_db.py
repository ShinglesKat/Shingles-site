import sqlite3
import os
import itertools
from flask import Blueprint

database_bp = Blueprint('databases', __name__)

def init_database(db_name, initialization_func=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    databases_dir = os.path.join(script_dir, '../databases')
    os.makedirs(databases_dir, exist_ok=True)
    db_path = os.path.join(databases_dir, db_name)
    
    print(f"[DB Init] Checking database: {db_name}")
    print(f"[DB Init] Full path: {db_path}")
    print(f"[DB Init] Database exists: {os.path.exists(db_path)}")
    
    if not os.path.exists(db_path):
        print(f"[DB Init] {db_name} not found, initializing...")
        connection = sqlite3.connect(db_path)
        try:
            schema_path = os.path.join(script_dir, '../schema.sql')
            print(f"[DB Init] Loading schema from: {schema_path}")
            
            with open(schema_path, 'r') as f:
                schema_content = f.read()
                print(f"[DB Init] Schema loaded, executing...")
                connection.executescript(schema_content)
            
            print(f"[DB Init] Schema executed successfully")
            
            cursor = connection.cursor()
            if initialization_func:
                print(f"[DB Init] Running initialization function: {initialization_func.__name__}")
                initialization_func(cursor)
                print(f"[DB Init] Initialization function completed")
            else:
                print(f"[DB Init] No initialization function provided")
            
            connection.commit()
            print(f"[DB Init] Database {db_name} initialized successfully")
            
        except sqlite3.Error as e:
            print(f"[DB Init ERROR] SQLite error occurred while initializing {db_name}: {e}")
        except FileNotFoundError as e:
            print(f"[DB Init ERROR] Schema file not found: {e}")
        except Exception as e:
            print(f"[DB Init ERROR] Unexpected error: {e}")
        finally:
            connection.close()
            print(f"[DB Init] Connection closed")
    else:
        print(f"[DB Init] {db_name} already exists, skipping initialization.")

def init_db():
    init_database('database.db')

def init_pixel_db():
    CELL_SIDE_COUNT = 50 # Assuming this is defined globally, or pass it in
    
    def setup_pixels(cursor):
        cursor.execute("SELECT COUNT(*) FROM pixels")
        count = cursor.fetchone()[0]

        if count == 0:
            print("Canvas is empty. Initializing all pixels to white.")
            default_pixels = [
                (x, y, '#ffffff', None) 
                for y, x in itertools.product(range(CELL_SIDE_COUNT), range(CELL_SIDE_COUNT))
            ]
            cursor.executemany(
                "INSERT INTO pixels (x, y, colour, ip_address) VALUES (?, ?, ?, ?)", 
                default_pixels
            )
        else:
            print(f"Canvas contains {count} pixels. Skipping default initialization.")
    init_database('pixels.db', setup_pixels)

def init_userinfo_db():
    init_database('userinfo.db')

def init_userdrawings_db():
    init_database('userdrawings.db')

def init_bannedips_db():
    init_database('bannedips.db')