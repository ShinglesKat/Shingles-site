import sqlite3
from config import CELL_SIDE_COUNT
from scripts import canvas_states
from scripts.config import DEFAULT_COLOUR
from scripts.hf_misc import get_db_connection


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