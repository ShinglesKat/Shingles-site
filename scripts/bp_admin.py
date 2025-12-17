import sqlite3
from flask import Blueprint, jsonify, request, session

from scripts.hf_misc import get_db_connection, parse_duration
from datetime import datetime, timezone

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route('/ban_ip', methods=['POST'])
def ban_ip():
    if session.get('accounttype') != 'admin':
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    ip_string = data.get('ip')
    reason = data.get('reason')
    ban_duration = data.get('ban_duration')

    if not ip_string or not reason or not ban_duration:
        return jsonify({'error': 'Missing IP, reason, or ban duration'}), 400

    try:
        duration_delta = parse_duration(ban_duration)
        expires_at = datetime.now(timezone.utc) + duration_delta
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

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
        return jsonify({'status': f'Banned {len(ips)} IP(s). Expires: {expires_at.isoformat()}'}), 200

    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'error': f'Database operation failed: {str(e)}'}), 500
    finally:
        conn.close()


@admin_bp.route('/userinfo')
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

@admin_bp.route('/update_user', methods=['POST'])
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