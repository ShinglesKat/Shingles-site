import sqlite3
import os
connection = sqlite3.connect('database.db')

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Now the working directory is where init_db.py is located, and file paths should work as expected
print(f"Current working directory: {os.getcwd()}")

with open('schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

try:
    cur.execute("INSERT INTO messages (username, content) VALUES (?, ?)",
                ('Test User', 'Content for the first post'))
    cur.execute("INSERT INTO messages (username, content) VALUES (?, ?)",
                ('Test User2', 'Content for the second post'))
    connection.commit()  # Make sure to commit after all inserts
except sqlite3.Error as e:
    print(f"Error occurred: {e}")

connection.close()


