import sqlite3
from threading import Lock, Thread
import time
from flask import Flask, session, redirect, request, jsonify, render_template, url_for
from markupsafe import escape
import os
from dotenv import load_dotenv

load_dotenv()
print("SECRET_KEY:", os.getenv('SECRET_KEY'))
print("ADMIN_PASSWORD:", os.getenv('ADMIN_PASSWORD'))

if not os.path.exists("database.db"):
    print("Pre-existing database not found...")
    from init_db import init_db
    init_db()

if not os.path.exists("pixels.db"):
    print("Pre-existing pixel database not found...")
    from init_db import init_pixel_db
    init_pixel_db()
    

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

def get_db_connections(db_name='database.db') -> sqlite3.Connection:
    conn = sqlite3.connect(db_name)
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
            #JOKE HERE --
            if session.get('brute'):
                username = 'brute'
                content = 'i am so gay!'
            
            # -----------
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
        
        
@app.route('/api/messages', methods=['GET'])
def get_messages():
    conn = get_db_connections()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM messages ORDER BY created DESC')
    messages = cursor.fetchall()
    conn.close()

    messages_list = []
    for msg in messages:
        msg_dict = dict(msg)
        if session.get('admin'):
            msg_dict['can_delete'] = True
        messages_list.append(msg_dict)

    return jsonify(messages_list)

@app.route('/login.html', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form['password'] == os.getenv('ADMIN_PASSWORD'):
        session['admin'] = True
        return redirect(url_for('home'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    conn = get_db_connections()
    cursor = conn.cursor()
    
    session.pop('admin', None)
    return redirect(url_for('home'))


@app.route('/canvas.html', methods=['GET'])
def canvas():
    return render_template('canvas.html', cell_side_count=CELL_SIDE_COUNT)

#For use in deleting comments        
@app.route('/delete/<int:message_id>', methods=['POST'])
def delete_message(message_id):
    if not session.get('admin'):
        return jsonify({"error": "You are not authorized to perform this action!"}), 403
    
    conn = get_db_connections()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('handle_messages'))

#CANVAS
CELL_SIDE_COUNT = 50
DEFAULT_COLOUR = "#ffffff"
saveInterval = 300

#Down here be jokes!
@app.route('/set_brute', methods=['POST'])
def set_brute():
    session['brute'] = True
    return jsonify({"session": "set to brute :)"}), 200

@app.route('/exit_brute')
def exit_brute():
    conn = get_db_connections()
    cursor = conn.cursor()
    
    session.pop('brute', None)
    return redirect(url_for('handle_messages'))


#Comment out if not local testing :)
if __name__ == '__main__':
    app.run(debug=True)
    
    
    
