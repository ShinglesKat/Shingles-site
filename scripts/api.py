import os
import json
import sqlite3
import time
import atexit
from datetime import datetime, timezone
from threading import Thread
from flask import Blueprint, jsonify, session
from config import CELL_SIDE_COUNT, SAVE_INTERVAL
from scripts.config import DEFAULT_COLOUR
from scripts.hf_bans import get_user_ip, handle_ban_check
from scripts.hf_misc import get_db_connection
from scripts.canvas_states import pendingUpdates, pixelArray

api_bp = Blueprint('api_bp', __name__)

def load_pixel_array():
    global pixelArray
    arr = [
        [{'colour': DEFAULT_COLOUR, 'ip_address': None} for _ in range(CELL_SIDE_COUNT)]
        for _ in range(CELL_SIDE_COUNT)
    ]

    try:
        conn = get_db_connection('pixels.db')
        cursor = conn.cursor()
        cursor.execute("SELECT x, y, colour, ip_address FROM pixels")
        for x, y, colour, ip_address in cursor.fetchall():
            if 0 <= x < CELL_SIDE_COUNT and 0 <= y < CELL_SIDE_COUNT:
                arr[y][x] = {'colour': colour, 'ip_address': ip_address}
        conn.close()
        pixelArray = arr
        print(f"[Startup] Loaded pixel array ({CELL_SIDE_COUNT}x{CELL_SIDE_COUNT})")
    except sqlite3.Error as e:
        print(f"[Startup ERROR] Failed to load pixel array: {e}")
        pixelArray = arr

    return pixelArray

pixelArray = load_pixel_array()

stop_thread = False

def flush_pending_updates():
    global pendingUpdates
    if not pendingUpdates:
        return

    updates_to_process = pendingUpdates[:]
    pendingUpdates.clear()

    try:
        conn = get_db_connection('pixels.db')
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT OR REPLACE INTO pixels (x, y, colour, ip_address)
            VALUES (?, ?, ?, ?)
            """,
            [(u['x'], u['y'], u['colour'], u['ip_address']) for u in updates_to_process]
        )
        conn.commit()
        conn.close()
        print(f"[Flush Thread] Flushed {len(updates_to_process)} pixel update(s)")
    except sqlite3.Error as e:
        print(f"[Flush Thread ERROR] Database error: {e}")
        if conn:
            conn.rollback()
            conn.close()
    except Exception as e:
        print(f"[Flush Thread ERROR] General error: {e}")
        if conn:
            conn.close()

def background_flush_loop():
    global stop_thread
    print(f"[Startup] Starting flush thread (Interval: {SAVE_INTERVAL}s)")
    while not stop_thread:
        flush_pending_updates()
        try:
            for _ in range(SAVE_INTERVAL):
                if stop_thread:
                    break
                time.sleep(1)
        except Exception:
            break
    print("[Shutdown] Flush thread stopped")

flush_thread = Thread(target=background_flush_loop, daemon=True)
flush_thread.start()

def graceful_shutdown():
    global stop_thread
    print("\n[Shutdown] Server shutdown detected. Flushing canvas...")
    stop_thread = True
    if flush_thread.is_alive():
        flush_thread.join(timeout=5)
    flush_pending_updates()
    print("[Shutdown] Canvas state saved")

atexit.register(graceful_shutdown)