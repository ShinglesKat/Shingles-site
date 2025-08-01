import os
import re
import json
import sqlite3
import time
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, session, redirect, url_for
from threading import Thread
from config import ADMIN_USERNAME, ADMIN_PASSWORD, SAVE_INTERVAL

api_bp = Blueprint('api_bp', __name__)

CELL_SIDE_COUNT = 50
DEFAULT_COLOUR = "#ffffff"
saveInterval = 300
pendingUpdates = []
pixelArray = []
    
def get_db_connection(db_name='database.db'):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    db_path = os.path.join(project_root, 'databases', db_name)
    print(f"Opening database at: {db_path}") 
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def parse_duration(duration):
    time_units = {
        'w': 7 * 24 * 60 * 60,
        'd': 24 * 60 * 60,
        'h': 60 * 60,
        'm': 60,
        's': 1,
    }
    pattern = r'(\d+)\s*(w|d|h|m|s)'
    matches = re.findall(pattern, duration.lower())
    
    if not matches:
        raise ValueError("Invalid duration format")
    
    total_seconds = sum(int(value) * time_units[unit] for value, unit in matches)
    return timedelta(seconds=total_seconds)

def load_pixel_array():
    arr = [[{'colour': DEFAULT_COLOUR, 'ip_address': None} for _ in range(CELL_SIDE_COUNT)] for _ in range(CELL_SIDE_COUNT)]
    conn = get_db_connection('pixels.db')
    cursor = conn.cursor()
    cursor.execute("SELECT x, y, colour, ip_address FROM pixels")
    for x, y, colour, ip_address in cursor.fetchall():
        if 0 <= x < CELL_SIDE_COUNT and 0 <= y < CELL_SIDE_COUNT:
            arr[y][x] = {'colour': colour, 'ip_address': ip_address}
    conn.close()
    return arr

pixelArray = load_pixel_array()
    
@api_bp.route('/get_session_data', methods=['GET'])
def get_session_data():
    if 'userid' in session and 'username' in session:
        return jsonify({
            'userid': session['userid'],
            'username': session['username'],
            'accounttype': session.get('accounttype')
        })
    else:
        return jsonify({'error': 'User not logged in'}), 401
    
@api_bp.route('/get_messages', methods=['GET'])
def get_messages():
    conn = get_db_connection('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM messages ORDER BY created DESC')
    messages = cursor.fetchall()
    conn.close()

    messages_list = []
    for msg in messages:
        msg_dict = dict(msg)
        if session.get('accounttype') == 'admin':
            msg_dict['can_delete'] = True
            msg_dict['can_ban'] = True
        messages_list.append(msg_dict)

    return jsonify(messages_list)

@api_bp.route('/post_message', methods=['POST'])

def handle_messages() -> jsonify:
    print("Request data:", request.form)
    conn = get_db_connection()
    cursor = conn.cursor()

    username = request.form.get('username', '').strip()
    content = request.form.get('content', '').strip()
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)  # Get IP address

    if not (1 < len(username) < 17):
        return jsonify({"error": "Username must be between 2 and 16 characters."}), 400
    if not (0 < len(content) < 200):
        return jsonify({"error": "Message must be under 200 characters."}), 400
    try:
        if session.get('brute'):
            username = 'brute'
            content = 'i am so gay!'
        # Updated to include IP address
        cursor.execute("INSERT INTO messages (username, content, ip_address) VALUES (?, ?, ?)", (username, content, user_ip))
        conn.commit()
        return jsonify({"status": "Message added successfully!"})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Database error? How did you even trigger this... Maybe stop trying to break it ;-;"}), 400
    finally:
        conn.close()

@api_bp.route('/delete_message/<int:message_id>', methods=['POST'])
def delete_message_api(message_id):
    if session.get('accounttype') != 'admin':
        return jsonify({"error": "You are not authorized to perform this action!"}), 403

    conn = get_db_connection('database.db') 
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "Message deleted successfully!"}), 200

@api_bp.route('/canvas/clear', methods=['POST'])
def clear_canvas():
    if session.get('accounttype') != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    conn = get_db_connection('pixels.db')
    cursor = conn.cursor()

    cursor.execute("UPDATE pixels SET colour = ? WHERE x BETWEEN 0 AND ? AND y BETWEEN 0 AND ?", (DEFAULT_COLOUR, CELL_SIDE_COUNT - 1, CELL_SIDE_COUNT - 1))
    conn.commit()

    cursor.execute("SELECT * FROM pixels WHERE colour != ?", (DEFAULT_COLOUR,))
    if remaining_pixels := cursor.fetchall():
        print("Pixels that weren't cleared:", remaining_pixels)

    global pixelArray
    pixelArray = [[{'colour': DEFAULT_COLOUR, 'ip_address': None} for _ in range(CELL_SIDE_COUNT)] for _ in range(CELL_SIDE_COUNT)]

    conn.close()

    return jsonify({"status": "Canvas cleared successfully!"}), 200

@api_bp.route('/save_drawing', methods=['POST'])
def upload_pixel_canvas():
    if 'userid' not in session or 'username' not in session:
        return jsonify({"error": "You must be logged in to save drawings."}), 401

    user_id = session['userid']
    username = session['username']

    data = request.get_json()
    print("Received data:", data)

    content = data.get('content')
    piece_name = data.get('piece_name')
    private = data.get('private')
    piece_id = data.get('piece_id')

    if not all([content, piece_name, private is not None]):
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db_connection('userdrawings.db')
    cursor = conn.cursor()
    new_piece = False
    try:
        if piece_id:
            # Validate ownership before updating
            cursor.execute("SELECT user_id FROM userdrawings WHERE id = ?", (piece_id,))
            existing = cursor.fetchone()
            if not existing:
                return jsonify({"error": "Drawing not found"}), 404
            if existing['user_id'] != user_id:
                return jsonify({"error": "You do not have permission to modify this drawing"}), 403

            cursor.execute("""
                UPDATE userdrawings 
                SET content = ?, private = ?, creationTime = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (content, private, piece_id))
            drawing_id = piece_id
        else:
            new_piece = True
            cursor.execute("""
                INSERT INTO userdrawings (user_id, username, piece_name, content, private) 
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, piece_name, content, private))
            drawing_id = cursor.lastrowid

        conn.commit()
        conn.close()

        if new_piece:
            conn = get_db_connection('userinfo.db')
            cursor = conn.cursor()
            cursor.execute("SELECT creationsIDs FROM userinfo WHERE id = ?", (user_id,))
            if result := cursor.fetchone():
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
            "id": drawing_id
        }), 200

    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


@api_bp.route('/retrieve_drawings', methods=['GET'])
def retrieve_drawings():
    limit = request.args.get('limit', type=int)  # No default
    conn = get_db_connection('userdrawings.db')
    cursor = conn.cursor()

    if limit is not None:
        cursor.execute("""
            SELECT * FROM userdrawings
            WHERE private = 0
            ORDER BY creationTime DESC
            LIMIT ?
        """, (limit,))
    else:
        cursor.execute("""
            SELECT * FROM userdrawings
            WHERE private = 0
            ORDER BY creationTime DESC
        """)

    drawings = cursor.fetchall()
    conn.close()
    return jsonify([dict(d) for d in drawings])

@api_bp.route('/delete_drawing/<int:drawing_id>', methods=['POST'])
def delete_drawing(drawing_id):
    if not session.get('accounttype'):
        return jsonify({"error": "Unauthorized"}), 403

    conn = get_db_connection('userdrawings.db')
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

    conn = get_db_connection('userinfo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT creationsIDs FROM userinfo WHERE id = ?", (drawing['user_id'],))
    if user_info := cursor.fetchone():
        creationsIDs = json.loads(user_info['creationsIDs'])
        if drawing_id in creationsIDs:
            creationsIDs.remove(drawing_id)
            cursor.execute("UPDATE userinfo SET creationsIDs = ? WHERE id = ?", (json.dumps(creationsIDs), drawing['user_id']))
            conn.commit()
    conn.close()

    return redirect(url_for('routes_bp.home'))

@api_bp.route('/get_user_drawings/<int:user_id>')
def get_user_drawings(user_id):
    conn = get_db_connection('userdrawings.db')
    cursor = conn.cursor()
    drawings = cursor.execute('SELECT * FROM userdrawings WHERE user_id = ?', (user_id,)).fetchall()

    drawings_list = []
    for drawing in drawings:
        drawing_dict = dict(drawing)
        try:
            # Ensure 'content' is parsed as JSON if it's a JSON string
            drawing_dict['drawing_content_json'] = json.loads(drawing_dict['content'])
        except (ValueError, TypeError):
            drawing_dict['drawing_content_json'] = [] # Default to empty list if content is not valid JSON or None
        drawings_list.append(drawing_dict)

    conn.close()
    return jsonify(drawings_list)

@api_bp.route('/userinfo')
def api_get_userinfo():
    user_id = request.args.get('id')
    username = request.args.get('username')

    if user_id:
        query = "SELECT * FROM userinfo WHERE id = ?"
        param = (user_id,)
    elif username:
        query = "SELECT * FROM userinfo WHERE username = ?"
        param = (username,)
    else:
        return jsonify({"error": "No user ID or username provided"}), 400

    conn = get_db_connection('userinfo.db')
    cursor = conn.cursor()
    cursor.execute(query, param)
    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(dict(user))

@api_bp.route('/update_user', methods=['POST'])
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

    conn = get_db_connection('userinfo.db')
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

@api_bp.route('/canvas/update', methods=['POST'])
def update_pixel():
    data = request.get_json()
    x = data.get('x')
    y = data.get('y')
    colour = data.get('colour')
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)

    if None in (x, y, colour):
        return jsonify({"error": "Missing data fields"}), 400
    if not (0 <= x < CELL_SIDE_COUNT and 0 <= y < CELL_SIDE_COUNT):
        return jsonify({"error": "Coordinates out of bounds"}), 400

    global pixelArray
    pixelArray[y][x] = {'colour': colour, 'ip_address': ip_address}
    print(f"[DEBUG] Parsed update: ({x}, {y}) -> {colour} from {ip_address}")
    pendingUpdates.append({'x': x, 'y': y, 'colour': colour, 'ip_address': ip_address})

    return jsonify({"status": "Pixel updated successfully"})

@api_bp.route('/canvas', methods=['GET'])
def get_pixel_array():
    return jsonify(pixelArray)

@api_bp.route('/ban_ip', methods=['POST'])
def ban_ip():
    if session.get('accounttype') != 'admin':
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json()
    ip_string = data.get('ip')
    reason = data.get('reason')
    ban_duration = data.get('ban_duration')

    if not ip_string or not reason or not ban_duration:
        return jsonify({"error": "Missing IP, reason, or ban duration"}), 400

    try:
        duration_delta = parse_duration(ban_duration)
        expires_at = datetime.now(timezone.utc) + duration_delta
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Split comma-separated IPs and sanitize
    ips = [ip.strip() for ip in ip_string.split(',') if ip.strip()]

    conn = get_db_connection('bannedips.db')
    cursor = conn.cursor()

    try:
        for ip in ips:
            cursor.execute("SELECT ip FROM bannedIPs WHERE ip = ?", (ip,))
            if existing_ban := cursor.fetchone():
                cursor.execute(
                    "UPDATE bannedIPs SET reason = ?, ban_duration = ?, ban_expires_at = ? WHERE ip = ?",
                    (reason, ban_duration, expires_at.isoformat(), ip)
                )
            else:
                cursor.execute(
                    "INSERT INTO bannedIPs (ip, reason, ban_duration, ban_expires_at) VALUES (?, ?, ?, ?)",
                    (ip, reason, ban_duration, expires_at.isoformat())
                )
        conn.commit()
        return jsonify({"status": f"Banned {len(ips)} IP(s). Expires: {expires_at.isoformat()}"}), 200

    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({"error": f"Database operation failed: {str(e)}"}), 500
    finally:
        conn.close()

@api_bp.route('/check_ban_status', methods=['GET'])
def check_ban_status():
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()

    conn = get_db_connection('bannedips.db')
    cursor = conn.cursor()

    now_utc = datetime.now(timezone.utc)
    now_iso = now_utc.isoformat()

    try:
        cursor.execute(
            "SELECT ban_expires_at, reason FROM bannedIPs WHERE ip = ? AND ban_expires_at > ?",
            (user_ip, now_iso)
        )
        if result := cursor.fetchone():
            return jsonify({
                "banned": True,
                "expires_at": result['ban_expires_at'],
                "reason": result['reason']
            }), 200
        # Check for expired ban to clean up
        cursor.execute(
            "SELECT ip FROM bannedIPs WHERE ip = ? AND ban_expires_at <= ?",
            (user_ip, now_iso)
        )
        if cursor.fetchone():
            try:
                cursor.execute("DELETE FROM bannedIPs WHERE ip = ?", (user_ip,))
                conn.commit()
                print(f"Cleaned up expired ban for IP: {user_ip}")
            except sqlite3.Error as e:
                conn.rollback()
                print(f"Error deleting expired ban for IP {user_ip}: {e}")

        return jsonify({"banned": False}), 200
    finally:
        conn.close()

@api_bp.route('/register_account', methods=['POST'])
def register_account():
    data = request.get_json()
    username = data.get('username', '').strip()
    password_hash = data.get('password')  # Assume password is already hashed client-side
    if not username or not password_hash:
        return jsonify({"error": "Username and password required"}), 400
    if len(username) < 2 or len(username) > 16:
        return jsonify({"error": "Username must be between 2 and 16 characters"}), 400

    conn = get_db_connection('userinfo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM userinfo WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": "Username already exists"}), 400

    try:
        cursor.execute("INSERT INTO userinfo (username, password, userType, creationsIDs) VALUES (?, ?, 'user', '[]')", (username, password_hash))
        conn.commit()
        return jsonify({"status": "Account registered successfully"})
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

@api_bp.route('/login', methods=['POST'])
def attempt_login():
    password = request.form.get('password', '').strip()
    username = request.form.get('username', '').strip()

    if username == os.getenv('ADMIN_USERNAME') and password == os.getenv('ADMIN_PASSWORD'):
        session['admin'] = True
        session['username'] = username
        session['accounttype'] = 'admin'
        return redirect(url_for('routes_bp.home'))

    conn = get_db_connection('userinfo.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM userinfo WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['username'] = username
        session['accounttype'] = user['userType']
        session['userid'] = user['id']
        return redirect(url_for('routes_bp.home'))
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@api_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    session.pop('admin', None)
    session.pop('accounttype', None)

    session.clear()
    return jsonify({"message": "Logged out successfully"})

__all__ = ['pendingUpdates', 'get_db_connection']