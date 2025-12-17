
import json
import sqlite3
from flask import Blueprint, jsonify, redirect, request, session, url_for

from scripts.hf_bans import handle_ban_check
from scripts.hf_misc import get_db_connection


singleplayer_canvas_bp = Blueprint('singeplayer_canvas_bp', __name__)

@singleplayer_canvas_bp.route('/save_drawing', methods=['POST'])
def upload_pixel_canvas():
    if ban_response := handle_ban_check(
        "You are banned from uploading images!"
    ):
        return ban_response

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
            cursor.execute("""
                SELECT id FROM userdrawings 
                WHERE user_id = ? AND piece_name = ?
            """, (user_id, piece_name))
            if existing_piece := cursor.fetchone():
                # Update the existing piece instead of inserting
                cursor.execute("""
                    UPDATE userdrawings
                    SET content = ?, private = ?, creationTime = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (content, private, existing_piece['id']))
                drawing_id = existing_piece['id']
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

@singleplayer_canvas_bp.route('/delete_drawing/<int:drawing_id>', methods=['POST'])
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