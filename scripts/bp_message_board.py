from flask import Blueprint, jsonify, request, session

from scripts.hf_bans import handle_ban_check
from scripts.hf_misc import get_db_connection


message_board_bp = Blueprint('message_board_bp', __name__)

@message_board_bp.route('/get_messages', methods=['GET'])
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

@message_board_bp.route('/post_message', methods=['POST'])
def handle_messages() -> jsonify:
    print("Request data:", request.form)
    conn = get_db_connection()
    cursor = conn.cursor()
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)  # Get IP address
    
    username = request.form.get('username', '').strip()
    content = request.form.get('content', '').strip()
    if ban_response := handle_ban_check(
        "You are banned from posting messages!"
    ):
        return ban_response

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

@message_board_bp.route('/delete_message/<int:message_id>', methods=['POST'])
def delete_message_api(message_id):
    if session.get('accounttype') != 'admin':
        return jsonify({"error": "You are not authorized to perform this action!"}), 403

    conn = get_db_connection('database.db') 
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "Message deleted successfully!"}), 200
