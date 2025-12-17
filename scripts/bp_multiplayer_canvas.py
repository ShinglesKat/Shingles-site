from flask import Blueprint, jsonify, request, session

from config import CELL_SIDE_COUNT
from scripts import canvas_states
from scripts.config import DEFAULT_COLOUR
from scripts.hf_bans import get_user_ip, handle_ban_check
from scripts.hf_misc import get_db_connection


multiplayer_canvas_bp = Blueprint('multiplayer_canvas_bp', __name__)

@multiplayer_canvas_bp.route('/canvas', methods=['GET'])
def get_pixel_array():
    return jsonify(canvas_states.pixelArray)

@multiplayer_canvas_bp.route('/canvas/clear', methods=['POST'])
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

@multiplayer_canvas_bp.route('/canvas/update', methods=['POST'])
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

@multiplayer_canvas_bp.route('/retrieve_drawings', methods=['GET'])
def retrieve_drawings():
    limit = request.args.get('limit', type=int)
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