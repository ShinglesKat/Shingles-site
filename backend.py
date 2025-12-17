from flask import Flask, session, redirect, request, jsonify, render_template, url_for
from scripts.hf_databases import (
    database_bp,
    init_database,
    init_pixel_db,
    init_db,
    init_userinfo_db,
    init_userdrawings_db,
    init_bannedips_db,
)

# init databases BEFORE DOING ANYTHING
init_db()
init_userinfo_db()
init_userdrawings_db()
init_bannedips_db()
init_pixel_db() 
from datetime import datetime, timedelta, timezone
import sqlite3
from threading import Lock, Thread
import time
import json
import os
import re
from flask_wtf import CSRFProtect

from markupsafe import escape
from dotenv import load_dotenv
from flask_talisman import Talisman
import requests
from config import SAVE_INTERVAL, SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD
from scripts.routes import routes_bp
from scripts.canvas_states import pendingUpdates
from scripts.api import api_bp, get_db_connection
# Boyfriend stuff :3
from config import FREEVIEW_PAGE, FREEVIEW_URL_PREFIX

# Thread management variables
_flush_thread = None
_flush_lock = Lock()
_thread_running = False

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.register_blueprint(database_bp)
app.register_blueprint(routes_bp)
app.register_blueprint(api_bp, url_prefix='/api')
csp = {
    'default-src': ["'self'"],
    'script-src': ["'self'"],
    'style-src': ["'self'", "'unsafe-inline'"],  
    'img-src': ["'self'", "data:"],
    'connect-src': ["'self'"],
}
Talisman(
    app,
    content_security_policy=csp,
    content_security_policy_nonce_in=['script'],
    referrer_policy='strict-origin-when-cross-origin',
    permissions_policy={
        "geolocation": [],
        "camera": [],
        "microphone": [],
    },
    force_https=True,
    strict_transport_security=True,
    strict_transport_security_preload=True,
    strict_transport_security_include_subdomains=True,
    frame_options=None,
    x_xss_protection=False,
)
def should_init_pixel_db():
    try:
        conn = get_db_connection('pixels.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM pixels")
        count = cursor.fetchone()[0]
        return count == 0
    except Exception as e:
        print(f"[DB CHECK ERROR] {e}")
        return False  # Don't initialize if unsure
    finally:
        conn.close()

if should_init_pixel_db():
    print("[Init] Pixel DB is empty, initializing...")
    init_pixel_db()
else:
    print("[Init] Pixel DB already has data, skipping init_pixel_db()")
    
def flush_pending_updates():
    global _thread_running
    _thread_running = True

    while _thread_running:
        try:
            time.sleep(SAVE_INTERVAL)

            with _flush_lock:
                print(f"[Flush Thread] Attempting to save {len(pendingUpdates)} pixels")

                if pendingUpdates:
                    pixels_to_save = pendingUpdates.copy()
                    pendingUpdates.clear()
                else:
                    print("[Flush Thread] No updates to flush")
                    continue

            update_pixel_db(pixels_to_save)
            print("[Flush Thread] Updated Database... (pixels.db)")

        except Exception as e:
            print(f"[Flush Thread ERROR] {e}")
            time.sleep(5)

# DB update function
def update_pixel_db(pixelArray):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    db_path = os.path.join(project_root, 'databases', 'pixels.db')
    print(f"[DB] Updating database at: {db_path}")
    
    conn = get_db_connection('pixels.db')
    cursor = conn.cursor()
    try:
        for pixel in pixelArray:
            x = pixel['x']
            y = pixel['y']
            colour = pixel['colour']
            ip_address = pixel.get('ip_address')
            print(f"Writing to DB: ({x}, {y}) = {colour}, IP: {ip_address}")
            cursor.execute("""
                INSERT INTO pixels (x, y, colour, ip_address)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(x, y)
                DO UPDATE SET colour = excluded.colour, ip_address = excluded.ip_address;
            """, (x, y, colour, ip_address))
        conn.commit()
    except Exception as e:
        print(f"[DB ERROR] {e}")
        conn.rollback()
    finally:
        conn.close()

def init_flush_thread():
    global _flush_thread, _thread_running
    
    with _flush_lock:
        if _flush_thread is not None and _flush_thread.is_alive():
            print("[Startup] Flush thread already running, skipping initialization")
            return
        
        print("[Startup] Starting background flush thread...")
        _thread_running = False
        time.sleep(0.1)
        
        _flush_thread = Thread(target=flush_pending_updates, daemon=True)
        _flush_thread.start()
        print("[Startup] Background flush thread started successfully!")

init_flush_thread()

if __name__ == '__main__':
    app.run(debug=True)
    