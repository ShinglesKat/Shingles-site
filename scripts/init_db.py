import sqlite3
import os
import itertools
from flask import Blueprint

database_bp = Blueprint('databases', __name__)

def init_database(db_name, initialization_func=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    databases_dir = os.path.join(project_root, 'databases')
    os.makedirs(databases_dir, exist_ok=True)
    db_path = os.path.join(databases_dir, db_name)
    
    if not os.path.exists(db_path):
        print(f"{db_name} not found, initializing...")
        connection = sqlite3.connect(db_path)
        try:
            # Look for schema.sql in the project root
            schema_path = os.path.join(project_root, 'schema.sql')
            if os.path.exists(schema_path):
                with open(schema_path, 'r') as f:
                    connection.executescript(f.read())
                print(f"Applied schema.sql to {db_name}")
            else:
                print(f"Warning: schema.sql not found at {schema_path}")
            
            cursor = connection.cursor()
            if initialization_func:
                initialization_func(cursor)
            connection.commit()
            print(f"Successfully initialized {db_name}")
        except sqlite3.Error as e:
            print(f"Error occurred while initializing {db_name}: {e}")
        except Exception as e:
            print(f"General error initializing {db_name}: {e}")
        finally:
            connection.close()
    else:
        print(f"{db_name} already exists, skipping initialization.")

def init_db():
    init_database('database.db')

def init_pixel_db():
    def setup_pixels(cursor):
        for y, x in itertools.product(range(50), range(50)):
            cursor.execute(
                "INSERT INTO pixels (x, y, colour, ip_address) VALUES (?, ?, ?, ?)",  # Fixed column name
                (x, y, '#ffffff', None)  # Added # prefix for consistency
            )
    init_database('pixels.db', setup_pixels)

def init_userinfo_db():
    init_database('userinfo.db')

def init_userdrawings_db():
    init_database('userdrawings.db')

def init_bannedips_db():
    init_database('bannedips.db')