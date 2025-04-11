import sqlite3
import os

def init_db():
    connection = sqlite3.connect('database.db')

    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print(f"Current working directory: {os.getcwd()}")

    with open('schema.sql') as f:
        connection.executescript(f.read())

    cursor = connection.cursor()

    try:
        cursor.execute("INSERT INTO messages (username, content) VALUES (?, ?)",
                    ('Shingle', 'Test content for first post :^)'))
        connection.commit()
    except sqlite3.Error as e:
        print(f"Error occurred: {e}")
    finally:
        connection.close()
