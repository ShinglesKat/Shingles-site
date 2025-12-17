import json
from flask import Blueprint, request, jsonify, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import hashlib
import os

from scripts.hf_misc import get_db_connection

account_handling_bp = Blueprint('account_handling_bp', __name__)

@account_handling_bp.route('/register_account', methods=['POST'])
def register_account():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()  # raw password

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    if len(username) < 2 or len(username) > 16:
        return jsonify({"error": "Username must be between 2 and 16 characters"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters!"}), 400

    password_hash = generate_password_hash(password)  # hash server-side

    conn = get_db_connection('userinfo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM userinfo WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": "Username already exists"}), 400

    try:
        cursor.execute(
            "INSERT INTO userinfo (username, password, userType, creationsIDs) VALUES (?, ?, 'user', '[]')",
            (username, password_hash)
        )
        conn.commit()
        return jsonify({"status": "Account registered successfully"})
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

@account_handling_bp.route('/login', methods=['POST'])
def attempt_login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()  # raw password from client

    # Check for admin login
    if username == os.getenv('ADMIN_USERNAME') and password == os.getenv('ADMIN_PASSWORD'):
        session['admin'] = True
        session['username'] = username
        session['accounttype'] = 'admin'
        return redirect(url_for('routes_bp.home'))

    # Connect to database
    conn = get_db_connection('userinfo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM userinfo WHERE username = ?", (username,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"error": "Invalid credentials"}), 401

    stored_hash = user['password']
    is_old_sha256 = len(stored_hash) == 64 and all(c in '0123456789abcdef' for c in stored_hash)

    if is_old_sha256:
        # Compare SHA-256 of submitted password to stored hash
        hashed_submit = hashlib.sha256(password.encode()).hexdigest()
        if hashed_submit == stored_hash:
            # Successful login: migrate password to secure hash
            new_hash = generate_password_hash(password)
            cursor.execute("UPDATE userinfo SET password = ? WHERE id = ?", (new_hash, user['id']))
            conn.commit()
            password_valid = True
        else:
            password_valid = False
    else:
        # Stored hash is a werkzeug hash, verify normally
        password_valid = check_password_hash(stored_hash, password)

    conn.close()

    if password_valid:
        session['username'] = username
        session['accounttype'] = user['userType']
        session['userid'] = user['id']
        return redirect(url_for('routes_bp.home'))
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@account_handling_bp.route('/reset_password', methods=['POST'])
def reset_password():
    # 1. Check if user is logged in
    if 'userid' not in session or 'username' not in session:
        return jsonify({"error": "You must be logged in to reset your password."}), 401

    data = request.get_json()
    current_password = data.get('current_password', '').strip()
    new_password = data.get('new_password', '').strip()
    user_id = session['userid']

    # 2. Input Validation
    if not current_password or not new_password:
        return jsonify({"error": "Current password and new password are required."}), 400
    if len(new_password) < 6:
        return jsonify({"error": "New password must be at least 6 characters!"}), 400
    if current_password == new_password:
        return jsonify({"error": "New password must be different from the current password."}), 400

    conn = get_db_connection('userinfo.db')
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT password FROM userinfo WHERE id = ?", (user_id,))
        user_record = cursor.fetchone()

        if not user_record:
            return jsonify({"error": "User record not found."}), 404

        stored_hash = user_record['password']
        if not check_password_hash(stored_hash, current_password):
            return jsonify({"error": "Invalid current password."}), 401
        new_password_hash = generate_password_hash(new_password)

        cursor.execute(
            "UPDATE userinfo SET password = ? WHERE id = ?",
            (new_password_hash, user_id)
        )
        conn.commit()
        return jsonify({"status": "Password successfully reset."}), 200

    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

@account_handling_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    session.pop('admin', None)
    session.pop('accounttype', None)

    session.clear()
    return jsonify({"message": "Logged out successfully"})

@account_handling_bp.route('/get_user_drawings/<int:user_id>')
def get_user_drawings(user_id):
    logged_in_user_id = session.get('userid')
    logged_in_user_account_type = session.get('accounttype')
    conn = get_db_connection('userdrawings.db')
    cursor = conn.cursor()

    if logged_in_user_id == user_id or logged_in_user_account_type == 'admin':
        # Logged-in user is the owner
        cursor.execute('SELECT * FROM userdrawings WHERE user_id = ?', (user_id,))
    else:
        # Not the owner
        cursor.execute('SELECT * FROM userdrawings WHERE user_id = ? AND private = 0', (user_id,))

    drawings = cursor.fetchall()
    conn.close()

    drawings_list = []
    for drawing in drawings:
        drawing_dict = dict(drawing)
        try:
            drawing_dict['drawing_content_json'] = json.loads(drawing_dict['content'])
        except (ValueError, TypeError):
            drawing_dict['drawing_content_json'] = []
        drawings_list.append(drawing_dict)

    return jsonify(drawings_list)