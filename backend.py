import sqlite3
from threading import Lock, Thread
import time
import json
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
    
if not os.path.exists("userinfo.db"):
    print("Pre-existing userinfo database not found...")
    from init_db import init_userinfo_db
    init_userinfo_db()

if not os.path.exists("userdrawings.db"):
    print("Pre-existing userdrawings database not found...")
    from init_db import init_userdrawings_db
    init_userdrawings_db()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
    
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/message')
def render_message_page():
    return render_template('message.html')

@app.route('/canvas')
def render_canvas_landing_page():
    return render_template('canvas.html')

@app.route('/live_canvas')
def render_live_canvas_page():
    return render_template('live_canvas.html', cell_side_count=CELL_SIDE_COUNT)

@app.route('/login')
def render_login_page():
    return render_template('login.html')

@app.route('/user')
def render_user_profile():
    user_id = request.args.get('id')

    if not user_id:
        return jsonify({"error": "No user ID provided"}), 400

    conn = get_db_connections('userinfo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM userinfo WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({"error": "User not found"}), 404

    return render_template('user_profile.html', user=user)

@app.route('/drawing')
def render_user_drawing():
    drawing_id = request.args.get('id')

    if not drawing_id:
        return jsonify({"error": "No drawing ID provided"}), 400

    conn = get_db_connections('userdrawings.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM userdrawings WHERE id = ?", (drawing_id,))
    drawing = cursor.fetchone()
    conn.close()

    if not drawing:
        return jsonify({"error": "Drawing not found"}), 404

    drawing_content = drawing['content']
    try:
        drawing_content_json = json.loads(drawing_content)
    except ValueError as e:
        return jsonify({"error": f"Failed to parse drawing content: {str(e)}"}), 400

    return render_template(
        'user_drawing.html',
        drawing=drawing,
        drawing_content_json=drawing_content_json,
        session_userid=session.get('userid'),
        session_accounttype=session.get('accounttype')
    )


@app.route('/admin', methods=['GET'])
def admin_panel():
    if session.get('accounttype') != 'admin':
        return jsonify({"error": "Access denied"}), 403

    conn = sqlite3.connect('userinfo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM userinfo")
    users = cursor.fetchall()
    return render_template('admin.html', users=users)


def get_db_connections(db_name='database.db') -> sqlite3.Connection:
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/get_user_drawings/<int:user_id>')
def get_user_drawing(user_id):
    conn = get_db_connections('userdrawings.db')
    cursor = conn.cursor()
    drawings = cursor.execute('SELECT * FROM userdrawings WHERE user_id = ?', (user_id,)).fetchall()
    
    drawings_list = []
    for drawing in drawings:
        drawing_dict = dict(drawing)
        try:
            drawing_dict['drawing_content_json'] = json.loads(drawing_dict['content'])
        except ValueError:
            drawing_dict['drawing_content_json'] = []
        drawings_list.append(drawing_dict)
    
    conn.close()
    return jsonify(drawings_list)
    

@app.route('/get_session_data', methods=['GET'])
def get_session_data():
    if 'userid' in session and 'username' in session:
        return jsonify({
            'userid': session['userid'],
            'username': session['username']
        })
    else:
        return jsonify({'error': 'User not logged in'}), 401
    
@app.route('/message/post_message', methods=['POST'])
def handle_messages() -> jsonify:
    conn = get_db_connections()
    cursor = conn.cursor()

    username = request.form.get('username', '').strip()
    content = request.form.get('content', '').strip()

    #Ensure valid username and content.
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
    
        
@app.route('/api/get_messages', methods=['GET'])
def get_messages():
    conn = get_db_connections()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM messages ORDER BY created DESC')
    messages = cursor.fetchall()
    conn.close()

    messages_list = []
    for msg in messages:
        msg_dict = dict(msg)
        if session.get('accounttype') == 'admin':
            msg_dict['can_delete'] = True
        messages_list.append(msg_dict)

    return jsonify(messages_list)

#For use in deleting comments        
@app.route('/delete/<int:message_id>', methods=['POST'])
def delete_message(message_id):
    if session.get('accounttype') != 'admin':
        return jsonify({"error": "You are not authorized to perform this action!"}), 403
    
    conn = get_db_connections()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('render_message_page'))


#Login Stuff

@app.route('/register_account', methods=['POST'])
def register_account():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return jsonify({"error": "Failed to register account!"}), 403

    conn = get_db_connections('userinfo.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM userinfo WHERE username = ?", (username,))
    if cursor.fetchone():
        return jsonify({"error": "Failed to register account! Name already taken..."}), 403

    # Insert user with hashed password
    cursor.execute("INSERT INTO userinfo (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()
    return jsonify({"status": "Account successfully registered!"}), 200


@app.route('/login', methods=['POST'])
def attempt_login():
    password = request.form.get('password', '').strip()
    username = request.form.get('username', '').strip()

    #Check if attempting to login as admin user, useful for when server restarts and 0 accounts.
    if username == os.getenv('ADMIN_USERNAME') and password == os.getenv('ADMIN_PASSWORD'):
        session['admin'] = True
        session['username'] = username
        session['accounttype'] = 'admin'
        return redirect(url_for('home'))

    conn = get_db_connections('userinfo.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM userinfo WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['username'] = username
        session['accounttype'] = user['userType']
        session['userid'] = user['id']
        return redirect(url_for('home'))
    else:
        return jsonify({"error": "Invalid credentials"}), 401


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('admin', None)
    session.pop('accounttype', None)

    # Redirect to home or another page after logout
    return redirect(url_for('home'))


#LIVE CANVAS
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
        pendingUpdates.clear()
        print("Updated Database... (pixels.db)")
Thread(target=flush_pending_updates, daemon=True).start()

def update_pixel_db(pixelArray):
    conn = get_db_connections('pixels.db')
    cursor = conn.cursor()
    
    for pixel in pixelArray:
        x, y, colour = pixel

        #Update the color for the specific pixel (x, y)
        cursor.execute("SELECT 1 FROM pixels WHERE x = ? AND y = ?", (x, y))
        exists = cursor.fetchone()

        if exists:
            cursor.execute("UPDATE pixels SET colour = ? WHERE x = ? AND y = ?", (colour, x, y))
        else:
            cursor.execute("INSERT INTO pixels (x, y, colour) VALUES (?, ?, ?)", (x, y, colour))

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


#REGULAR CANVAS

@app.route('/upload', methods=['POST'])
def upload_pixel_canvas():
    data = request.get_json()
    print("Received data:", data)  # Debugging
    user_id = data.get('user_id')
    username = data.get('username')
    content = data.get('content')
    piece_name = data.get('piece_name')
    private = data.get('private')
    piece_id = data.get('piece_id')

    if not all([user_id, username, content, piece_name, private is not None]):
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db_connections('userdrawings.db')
    cursor = conn.cursor()
    new_piece = False
    try:
        #Check if drawing with same name exists
        cursor.execute("SELECT id FROM userdrawings WHERE user_id = ? AND piece_name = ?", (user_id, piece_name))
        existing_piece = cursor.fetchone()

        if existing_piece:
            drawing_id = existing_piece['id']
            cursor.execute("""
                UPDATE userdrawings 
                SET content = ?, private = ?, creationTime = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (content, private, drawing_id))
        else:
            new_piece = True
            cursor.execute("""
                INSERT INTO userdrawings (user_id, username, piece_name, content, private) 
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, piece_name, content, private))
            drawing_id = cursor.lastrowid

        conn.commit()
        conn.close()

        #if new drawing, add it into user's created
        if new_piece:
            conn = get_db_connections('userinfo.db')
            cursor = conn.cursor()
            cursor.execute("SELECT creationsIDs FROM userinfo WHERE id = ?", (user_id,))
            result = cursor.fetchone()

            if result:
                creations_list = json.loads(result['creationsIDs']) if result['creationsIDs'] else []
                creations_list.append(drawing_id)
                updated_creations_json = json.dumps(creations_list)

                cursor.execute("""
                    UPDATE userinfo
                    SET creationsIDs = ?
                    WHERE id = ?
                """, (updated_creations_json, user_id))
                conn.commit()
            conn.close()

        return jsonify({
            "message": "Canvas saved/updated successfully!",
            "piece_id": drawing_id
        }), 200
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@app.route('/retrieve_latest', methods=['GET'])
def retrieve_latest():
    conn = get_db_connections('userdrawings.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM userdrawings
        WHERE private = 0
        ORDER BY creationTime DESC
        LIMIT 5
    """)
    
    drawings = cursor.fetchall()
    conn.close()

    #Return the drawings as a list of dictionaries
    drawings_list = []
    for drawing in drawings:
        drawing_dict = dict(drawing)
        drawings_list.append(drawing_dict)

    return jsonify(drawings_list)

#Admin related
@app.route('/delete_drawing/<int:drawing_id>', methods=['POST'])
def delete_drawing(drawing_id):
    if not session.get('accounttype'):
        return jsonify({"error": "Unauthorized"}), 403

    conn = get_db_connections('userdrawings.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM userdrawings WHERE id = ?", (drawing_id,))
    drawing = cursor.fetchone()

    if not drawing:
        conn.close()
        return jsonify({"error": "Drawing not found"}), 404

    if session.get('accounttype') != 'admin' and session.get('userid') != drawing['user_id']:
        conn.close()
        return jsonify({"error": "Unauthorized"}), 403

    cursor.execute("DELETE FROM userdrawings WHERE id = ?", (drawing_id,))
    conn.commit()
    conn.close()
    
    conn = get_db_connections('userinfo.db')
    cursor = conn.cursor()
    owner_id = drawing['user_id']
    
    cursor.execute("SELECT creationsIDs FROM userinfo WHERE id = ?", (owner_id,))
    user_info = cursor.fetchone()
    
    if user_info:
        creationsIDs = json.loads(user_info['creationsIDs'])
        if drawing_id in creationsIDs:
            creationsIDs.remove(drawing_id)
            updated_creationsIDs = json.dumps(creationsIDs)
            cursor.execute("UPDATE userinfo SET creationsIDs = ? WHERE id = ?",(updated_creationsIDs, owner_id))
            conn.commit()
    conn.close()
            

    return redirect(url_for('home'))


@app.route('/api/userinfo')
def api_get_userinfo():
    user_id = request.args.get('id')

    if not user_id:
        return jsonify({"error": "No user ID provided"}), 400

    conn = get_db_connections('userinfo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM userinfo WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(dict(user))

@app.route('/api/update_user', methods=['POST'])
def update_user():
    if session.get('accounttype') != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    user_id = data.get('id')
    new_username = data.get('username')
    new_password = data.get('hashed_password')
    new_type = data.get('userType')
    new_drawings = data.get('userDrawings')

    if not (user_id and new_username and new_password and new_type and new_drawings):
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db_connections('userinfo.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE userinfo SET username = ?, password = ?, userType = ?, creationsIDs = ? WHERE id = ?",
            (new_username, new_password, new_type, new_drawings, user_id))

        conn.commit()
        return jsonify({"status": "User updated successfully"})
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


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
    return redirect(url_for('home'))


#Comment out if not local testing :)
if __name__ == '__main__':
    app.run(debug=True)
    
    
    
