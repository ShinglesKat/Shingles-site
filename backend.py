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
pendingUpdates = []
pixelArray=[]

        
def load_pixel_array():
    arr = [[DEFAULT_COLOUR for _ in range(CELL_SIDE_COUNT)] for _ in range(CELL_SIDE_COUNT)]
    conn = get_db_connections('pixels.db')
    cursor = conn.cursor()
    cursor.execute("SELECT x, y, colour FROM pixels")
    for x, y, colour in cursor.fetchall():
        if 0 <= x < CELL_SIDE_COUNT and 0 <= y < CELL_SIDE_COUNT:
            arr[y][x] = colour
        conn.close()
        return arr
pixelArray = load_pixel_array()

#save to database every 120 seconds, flush all lines waiting to be updated, my apologies if you're drawing at that time :)
def flush_pending_updates():
    while True:
        time.sleep(120)
        update_pixel_db(pendingUpdates)
        pendingUpdates = []
        print("Updated Database... (pixels.db)")
Thread(target=flush_pending_updates, daemon=True).start()

def update_pixel_db(pixelArray):
    conn = get_db_connections('pixels.db')
    cursor = conn.cursor()
    
    for pixel in pixelArray:
        x, y, colour = pixel

        #Update the color for the specific pixel (x, y)
        cursor.execute("""
            INSERT INTO pixels (x, y, colour) 
            VALUES (?, ?, ?) 
            ON CONFLICT(x, y) 
            DO UPDATE SET colour = ?;
        """, (x, y, colour, colour))

    conn.commit()
    conn.close()

@app.route('/canvas/updatePixel', methods=['POST'])
def update_pixel():
    data = request.get_json()
    x = data.get("x")
    y = data.get("y")
    colour = data.get("colour")
    
    if x is None or y is None or colour is None:
        return jsonify({"error": "Missing pixel data"}), 400
    
    if 0 <= x < CELL_SIDE_COUNT and 0 <= y < CELL_SIDE_COUNT:
        pixelArray[y][x] = colour
        pendingUpdates.append((x, y, colour))
        return jsonify({"status": "Pixel updated in memory"}), 200
    else:
        return jsonify({"error": "Invalid coordinates"}), 400

#this canvas clear was a pain in my ass and harder than I thought it'd be -.-
@app.route('/canvas/clear', methods=['POST'])
def clear_canvas():
    conn = get_db_connections('pixels.db')
    cursor = conn.cursor()

    #Reset all pixels to white in the database
    cursor.execute("UPDATE pixels SET colour = ? WHERE x BETWEEN 0 AND ? AND y BETWEEN 0 AND ?", (DEFAULT_COLOUR, CELL_SIDE_COUNT - 1, CELL_SIDE_COUNT - 1))
    conn.commit()

    #Ensure all pixels cleared correctly.
    cursor.execute("SELECT * FROM pixels WHERE colour != ?", (DEFAULT_COLOUR,))
    if remaining_pixels := cursor.fetchall():
        print("Pixels that weren't cleared:", remaining_pixels)

    #
    global pixelArray
    pixelArray = [[DEFAULT_COLOUR for _ in range(CELL_SIDE_COUNT)] for _ in range(CELL_SIDE_COUNT)]

    conn.close()

    return jsonify({"status": "Canvas cleared successfully!"}), 200

@app.route('/api/canvas', methods=['GET'])
def get_pixel_array():
    return jsonify(pixelArray)

@app.route('/canvas.html', methods=['GET'])
def canvas():
    return render_template('canvas.html', cell_side_count=CELL_SIDE_COUNT)

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
    
    
    
