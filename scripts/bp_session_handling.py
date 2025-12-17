from flask import Blueprint, jsonify, session

from scripts.hf_bans import handle_ban_check


session_handling_bp = Blueprint('session_handling_bp', __name__)

@session_handling_bp.route('/get_session_data', methods=['GET'])
def get_session_data():
    if 'userid' in session and 'username' in session:
        return jsonify({
            'userid': session['userid'],
            'username': session['username'],
            'accounttype': session.get('accounttype')
        })
    else:
        return jsonify({'error': 'User not logged in'}), 401
    

@session_handling_bp.route('/check_ban_status', methods=['GET'])
def check_ban_status():
    try:
        ban_response = handle_ban_check("You are banned from using this service.")
        return ban_response or (jsonify({'banned': False}), 200)
    except Exception as e:
        print(f"[BAN STATUS CHECK ERROR] {e}")
        return jsonify({'error': 'Could not check ban status'}), 500