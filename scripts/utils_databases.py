import itertools
import os
import sqlite3
from flask import Blueprint

from config import CELL_SIDE_COUNT

database_bp = Blueprint('databases', __name__)


def _table_exists(connection, table_name):
    cursor = connection.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cursor.fetchone() is not None


# Generic database initialiser
def init_database(db_name, initialization_func=None, check_table=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    databases_dir = os.path.join(script_dir, '../databases')
    os.makedirs(databases_dir, exist_ok=True)
    db_path = os.path.join(databases_dir, db_name)

    print(f"[DB Init] Checking database: {db_name}")
    print(f"[DB Init] Full path: {db_path}")

    connection = sqlite3.connect(db_path)
    try:
        needs_init = True
        if check_table:
            needs_init = not _table_exists(connection, check_table)

        print(f"[DB Init] {db_name} needs schema init: {needs_init}")

        if needs_init:
            schema_path = os.path.join(script_dir, '../schema.sql')
            print(f"[DB Init] Loading schema from: {schema_path}")
            with open(schema_path, 'r') as f:
                schema_content = f.read()
                print("[DB Init] Schema loaded, executing...")
                connection.executescript(schema_content)
            print("[DB Init] Schema executed successfully")

            if initialization_func:
                print(f"[DB Init] Running initialization function: {initialization_func.__name__}")
                initialization_func(connection.cursor())
                print("[DB Init] Initialization function completed")
            else:
                print("[DB Init] No initialization function provided")

            connection.commit()
            print(f"[DB Init] Database {db_name} initialized successfully")
        else:
            print(f"[DB Init] {db_name} already initialized, skipping.")

    except sqlite3.Error as e:
        print(f"[DB Init ERROR] SQLite error: {e}")
    except FileNotFoundError as e:
        print(f"[DB Init ERROR] Schema file not found: {e}")
    except Exception as e:
        print(f"[DB Init ERROR] Unexpected error: {e}")
    finally:
        connection.close()
        print("[DB Init] Connection closed")


# Per-database init helpers
def init_db():
    init_database('database.db', check_table='messages')


def init_pixel_db():
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
                default_pixels,
            )
        else:
            print(f"Canvas contains {count} pixels. Skipping default initialization.")

    init_database('pixels.db', setup_pixels, check_table='pixels')


def init_userinfo_db():
    init_database('userinfo.db', check_table='userinfo')


def init_userdrawings_db():
    init_database('userdrawings.db', check_table='userdrawings')


def init_bannedips_db():
    init_database('bannedips.db', check_table='bannedIPs')