import sqlite3
from flask import Flask, request, jsonify, render_template
from markupsafe import escape
import os

if not os.path.exists("database.db"):
    from init_db import init_db
    init_db()

app = Flask(__name__)

def get_db_connections() -> sqlite3.Connection:
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn
    
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/message.html', methods=['GET', 'POST'])
def handle_messages() -> jsonify:
    conn = get_db_connections()
    cursor = conn.cursor()

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        content = request.form.get('content', '').strip()

        if not (1 < len(username) < 17):
            return jsonify({"error": "Username must be between 2 and 16 characters."}), 400
        if not (0 < len(content) < 200):
            return jsonify({"error": "Message must be under 200 characters."}), 400

        try:
            cursor.execute("INSERT INTO messages (username, content) VALUES (?, ?)", (username, content))
            conn.commit()
            return jsonify({"status": "Message added successfully!"})
        except sqlite3.IntegrityError:
            return jsonify({"error": "Database error? How did you even trigger this... Maybe stop trying to break it ;-;"}), 400
        finally:
            conn.close()

    elif request.method == 'GET':
        cursor.execute('SELECT * FROM messages')
        messages = cursor.fetchall()
        conn.close()

        messages_dicts = [dict(msg) for msg in messages]
        return render_template('message.html', messages=messages_dicts)
    else:
        jsonify({"error": "Invalid request method"}), 400