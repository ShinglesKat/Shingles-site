import os
import re
import json
import sqlite3
import time
import atexit
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, session, redirect, url_for
from threading import Thread
from werkzeug.security import generate_password_hash, check_password_hash
from config import ADMIN_USERNAME, ADMIN_PASSWORD, CELL_SIDE_COUNT, SAVE_INTERVAL
from scripts.config import DEFAULT_COLOUR
from scripts.hf_bans import get_user_ip, handle_ban_check
from scripts.hf_misc import get_db_connection, parse_duration
from scripts.canvas_states import pendingUpdates, pixelArray

api_bp = Blueprint('api_bp', __name__)

def load_pixel_array():
    global pixelArray
    arr = [[{'colour': DEFAULT_COLOUR, 'ip_address': None} for _ in range(CELL_SIDE_COUNT)] for _ in range(CELL_SIDE_COUNT)]
    
    try:
        conn = get_db_connection('pixels.db')
        cursor = conn.cursor()
        cursor.execute("SELECT x, y, colour, ip_address FROM pixels")
        for x, y, colour, ip_address in cursor.fetchall():
            if 0 <= x < CELL_SIDE_COUNT and 0 <= y < CELL_SIDE_COUNT:
                arr[y][x] = {'colour': colour, 'ip_address': ip_address}
        conn.close()
        pixelArray = arr
        print(f"Loaded pixel array with {CELL_SIDE_COUNT}x{CELL_SIDE_COUNT} pixels")
    except sqlite3.Error as e:
        print(f"Error loading pixel array: {e}")
        # Initialize with default values if database isn't ready
        pixelArray = arr
    
    return pixelArray

pixelArray = load_pixel_array()

def flush_pending_updates():
    global pendingUpdates
    if not pendingUpdates:
        print("[Flush Thread] No pending updates to flush.")
        return
        
    updates_to_process = pendingUpdates[:]
    pendingUpdates.clear()

    conn = None
    try:
        conn = get_db_connection('pixels.db')
        cursor = conn.cursor()
        sql = """
        INSERT OR REPLACE INTO pixels (x, y, colour, ip_address) 
        VALUES (?, ?, ?, ?)
        """
        
        data = [
            (update['x'], update['y'], update['colour'], update['ip_address'])
            for update in updates_to_process
        ]
        
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
            for _ in range(SAVE_INTERVAL // 1):
                if stop_thread:
                    break
                time.sleep(1)
        except Exception:
            break
    print("[Shutdown] Background flush thread stopped.")

flush_thread = Thread(target=background_flush_loop)
flush_thread.daemon = True
flush_thread.start()
print("[Startup] Background flush thread started successfully!")

__all__ = ['pendingUpdates', 'get_db_connection', 'stop_thread', 'flush_pending_updates', 'flush_thread']

def graceful_shutdown():
    global stop_thread
    print("\n[Shutdown Hook] Server shutdown detected. Forcing final data flush...")
    stop_thread = True 
    
    if flush_thread.is_alive():
        flush_thread.join(timeout=5) # Wait up to 5 seconds
    
    flush_pending_updates() 
    print("[Shutdown Hook] Final flush complete. Canvas state saved to disk.")

atexit.register(graceful_shutdown)
