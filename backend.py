from scripts.init_db import (
    database_bp,
    init_database,
    init_pixel_db,
    init_db,
    init_userinfo_db,
    init_userdrawings_db,
    init_bannedips_db,
)

# init databases BEFORE DOING ANYTHING
init_pixel_db()
init_db()
init_userinfo_db()
init_userdrawings_db()
init_bannedips_db()

from datetime import datetime, timedelta, timezone
import sqlite3
from threading import Lock, Thread
import time
import json
import os
import re

from flask_wtf import CSRFProtect
from flask import Flask, session, redirect, request, jsonify, render_template, url_for
from markupsafe import escape
from dotenv import load_dotenv
from flask_talisman import Talisman
import requests


from config import SAVE_INTERVAL, SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD

from scripts.routes import routes_bp
from scripts.api import api_bp, pendingUpdates, get_db_connection

#boyfriend stuff :3
from config import FREEVIEW_PAGE, FREEVIEW_URL_PREFIX

app = Flask(__name__)
app.secret_key = SECRET_KEY

app.register_blueprint(database_bp)



app.register_blueprint(routes_bp)
app.register_blueprint(api_bp, url_prefix='/api')



#csrf = CSRFProtect(app)
csp = {
    'default-src': ["'self'"],
    'script-src': ["'self'"], 
    'style-src': ["'self'", "'unsafe-inline'"], 
    'img-src': ["'self'", "data:"],
    'connect-src': ["'self'"],
}

# Initialize Talisman with headers
Talisman(app,
            content_security_policy=csp,
            content_security_policy_nonce_in=['script'],
            referrer_policy='strict-origin-when-cross-origin',
            permissions_policy={
                "geolocation": [],
                "camera": [],
                "microphone": [],
            })


def flush_pending_updates():
    global pendingUpdates
    while True:
        time.sleep(SAVE_INTERVAL)
        print(f"[Flush Thread] Attempting to save {len(pendingUpdates)} pixels")
        if pendingUpdates:
            update_pixel_db(pendingUpdates)
            pendingUpdates = []
            print("[Flush Thread] Updated Database... (pixels.db)")
        else:
            print("[Flush Thread] No updates to flush")


Thread(target=flush_pending_updates, daemon=True).start()
def update_pixel_db(pixelArray):
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
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)