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

    if not os.path.exists(db_path):
        print(f"{db_name} not found, initializing...")
        connection = sqlite3.connect(db_path)
        try:
            schema_path = os.path.join(script_dir, '../schema.sql')
            with open(schema_path, 'r') as f:
                connection.executescript(f.read())

            cursor = connection.cursor()

            if initialization_func:
                initialization_func(cursor)

            connection.commit()
        except sqlite3.Error as e:
            print(f"Error occurred while initializing {db_name}: {e}")
        finally:
            connection.close()
    else:
        print(f"{db_name} already exists, skipping initialization.")

def init_db():
    def initializer(cursor):
        cursor.execute(
            "INSERT INTO messages (username, content) VALUES (?, ?)",
            ('Shingle', 'Test content for first post :^)')
        )
    init_database('database.db', initializer)

def init_pixel_db():
    def initializer(cursor):
        for y, x in itertools.product(range(10), range(10)):
            cursor.execute(
                "INSERT INTO pixels (x, y, colour) VALUES (?, ?, ?)",
                (x, y, 'FFFFFF')
            )
    init_database('pixels.db', initializer)

def init_userinfo_db():
    init_database('userinfo.db')

def init_userdrawings_db():
    init_database('userdrawings.db')

def init_bannedips_db():
    init_database('bannedips.db')
