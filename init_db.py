import itertools
import sqlite3
import os

def init_database(db_name, initialization_func=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    db_path = os.path.join(script_dir, db_name)

    if not os.path.exists(db_path):
        print(f"{db_name} not found, initializing...")
        connection = sqlite3.connect(db_path)
        try:
            with open('schema.sql') as f:
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
    def setup_messages(cursor):
        cursor.execute(
            "INSERT INTO messages (username, content) VALUES (?, ?)",
            ('Shingle', 'Test content for first post :^)')
        )

    init_database('database.db', setup_messages)

def init_pixel_db():
    def setup_pixels(cursor):
        for y, x in itertools.product(range(10), range(10)):
            cursor.execute(
                "INSERT INTO pixels (x, y, colour) VALUES (?, ?, ?)",
                (x, y, 'FFFFFF')
            )

    init_database('pixels.db', setup_pixels)

def init_userinfo_db():
    init_database('userinfo.db')

def init_userdrawings_db():
    init_database('userdrawings.db')
