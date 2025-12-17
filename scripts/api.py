import os
import re
import json
import sqlite3
import time
import atexit
from datetime import datetime, timezone, timedelta
from threading import Thread
from flask import Blueprint, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from config import ADMIN_USERNAME, ADMIN_PASSWORD, CELL_SIDE_COUNT, SAVE_INTERVAL
from scripts.config import DEFAULT_COLOUR
from scripts.hf_bans import get_user_ip, handle_ban_check
from scripts.hf_misc import get_db_connection, parse_duration
import scripts.canvas_states as canvas_states

api_bp = Blueprint('api_bp', __name__)

def load_pixel_array():
    arr = [[{'colour': DEFAULT_COLOUR, 'ip_address': None} for _ in range(CELL_SIDE_COUNT)] for _ in range(CELL_SIDE_COUNT)]
    try:
        conn = get_db_connection('pixels.db')
        cursor = conn.cursor()
        cursor.execute("SELECT x, y, colour, ip_address FROM pixels")
        for x, y, colour, ip_address in cursor.fetchall():
            if 0 <= x < CELL_SIDE_COUNT and 0 <= y < CELL_SIDE_COUNT:
                arr[y][x] = {'colour': colour, 'ip_address': ip_address}
        conn.close()
        canvas_states.pixelArray[:] = arr
        print(f"Loaded pixel array with {CELL_SIDE_COUNT}x{CELL_SIDE_COUNT} pixels")
    except sqlite3.Error as e:
        print(f"Error loading pixel array: {e}")
        canvas_states.pixelArray[:] = arr  # fallback
    return canvas_states.pixelArray

canvas_states.pixelArray[:] = load_pixel_array()

def flush_pending_updates():
    if not canvas_states.pendingUpdates:
        print("[Flush Thread] No pending updates to flush.")
        return
    
    updates_to_process = canvas_states.pendingUpdates[:]
    canvas_states.pendingUpdates.clear()

    conn = None
    try:
        conn = get_db_connection('pixels.db')
        cursor = conn.cursor()
        sql = """
        INSERT OR REPLACE INTO pixels (x, y, colour, ip_address) 
        VALUES (?, ?, ?, ?)
        """
        data = [(u['x'], u['y'], u['colour'], u['ip_address']) for u in updates_to_process]
        cursor.executemany(sql, data)
        conn.commit()
        print(f"[Flush Thread] Successfully flushed {len(updates_to_process)} pixel update(s).")
    except sqlite3.Error as e:
        print(f"[Flush Thread ERROR] Database error during flush: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"[Flush Thread ERROR] General error during flush: {e}")
    finally:
        if conn:
            conn.close()

stop_thread = False

def background_flush_loop():
    global stop_thread
    print(f"[Startup] Starting background flush thread (Interval: {SAVE_INTERVAL}s)...")
    while not stop_thread:
        flush_pending_updates()
        try:
            for _ in range(SAVE_INTERVAL):
                if stop_thread:
                    break
                time.sleep(1)
        except Exception:
            break
    print("[Shutdown] Background flush thread stopped.")

flush_thread = Thread(target=background_flush_loop, daemon=True)
flush_thread.start()
print("[Startup] Background flush thread started successfully!")

@api_bp.route('/get_session_data', methods=['GET'])
def get_session_data():
    if 'userid' in session and 'username' in session:
        return jsonify({
            'userid': session['userid'],
            'username': session['username'],
            'accounttype': session.get('accounttype')
        })
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
def handle_messages():
    conn = get_db_connection()
    cursor = conn.cursor()
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    username = request.form.get('username', '').strip()
    content = request.form.get('content', '').strip()

    if ban_response := handle_ban_check("You are banned from posting messages!"):
        return ban_response

    if not (1 < len(username) < 17):
        return jsonify({"error": "Username must be between 2 and 16 characters."}), 400
    if not (0 < len(content) < 200):
        return jsonify({"error": "Message must be under 200 characters."}), 400

    try:
        if session.get('brute'):
            username = 'brute'
            content = 'i am so gay!'

        cursor.execute("INSERT INTO messages (username, content, ip_address) VALUES (?, ?, ?)", 
                       (username, content, user_ip))
        conn.commit()
        return jsonify({"status": "Message added successfully!"})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Database error? Stop trying to break it ;-;"}), 400
    finally:
        conn.close()

@api_bp.route('/delete_message/<int:message_id>', methods=['POST'])
def delete_message_api(message_id):
    if session.get('accounttype') != 'admin':
        return jsonify({"error": "You are not authorized!"}), 403

    conn = get_db_connection('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "Message deleted successfully!"})

@api_bp.route('/canvas/clear', methods=['POST'])
def clear_canvas():
    if session.get('accounttype') != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    conn = get_db_connection('pixels.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE pixels SET colour = ? WHERE x BETWEEN 0 AND ? AND y BETWEEN 0 AND ?", 
                   (DEFAULT_COLOUR, CELL_SIDE_COUNT - 1, CELL_SIDE_COUNT - 1))
    conn.commit()
    conn.close()

    canvas_states.pixelArray[:] = [[{'colour': DEFAULT_COLOUR, 'ip_address': None} for _ in range(CELL_SIDE_COUNT)]
                                   for _ in range(CELL_SIDE_COUNT)]
    canvas_states.pendingUpdates.clear()
    return jsonify({"status": "Canvas cleared successfully!"})

@api_bp.route('/canvas/update', methods=['POST'])
def update_pixel():
    try:
        if ban_response := handle_ban_check("You are banned from drawing on the canvas."):
            return ban_response

        data = request.get_json()
        x = data.get('x')
        y = data.get('y')
        colour = data.get('colour')
        if None in (x, y, colour):
            return jsonify({'error': 'Missing data fields'}), 400
        if not (0 <= x < CELL_SIDE_COUNT and 0 <= y < CELL_SIDE_COUNT):
            return jsonify({'error': 'Coordinates out of bounds'}), 400

        pixel_data = {'colour': colour, 'ip_address': get_user_ip()}
        canvas_states.pixelArray[y][x] = pixel_data
        canvas_states.pendingUpdates.append({'x': x, 'y': y, **pixel_data})

        return jsonify({'status': 'Pixel updated successfully'}), 200
    except Exception as e:
        print(f"[CANVAS UPDATE ERROR] {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/canvas', methods=['GET'])
def get_pixel_array():
    return jsonify(canvas_states.pixelArray)

def graceful_shutdown():
    global stop_thread
    print("\n[Shutdown Hook] Server shutdown detected. Forcing final data flush...")
    stop_thread = True
    if flush_thread.is_alive():
        flush_thread.join(timeout=5)
    flush_pending_updates()
    print("[Shutdown Hook] Final flush complete. Canvas state saved to disk.")

atexit.register(graceful_shutdown)
