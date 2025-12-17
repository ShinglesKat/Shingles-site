import os
import json
import sqlite3
import requests
from flask import Blueprint, render_template, redirect, request, session, send_from_directory

from config import FREEVIEW_PAGE, FREEVIEW_URL_PREFIX, CELL_SIDE_COUNT
from scripts.hf_misc import get_db_connection

routes_bp = Blueprint('routes_bp', __name__)

@routes_bp.route('/favicon.ico')
def favicon():
    return send_from_directory('static/images', 'favicon.ico')# General pages
@routes_bp.route('/')
def home():
    return render_template('index.html')

@routes_bp.route('/login', methods=['GET'])
def render_login_page():
    return render_template('login.html')

@routes_bp.route('/message')
def render_message_page():
    return render_template('message.html')

# Canvas & Drawing pages
@routes_bp.route('/canvas')
def render_canvas_landing_page():
    return render_template('canvas.html')

@routes_bp.route('/live_canvas')
def render_live_canvas_page():
    return render_template('live_canvas.html', cell_side_count=CELL_SIDE_COUNT)

@routes_bp.route('/drawing')
def render_user_drawing_page():
    drawing_id = request.args.get('id')
    if not drawing_id:
        return {"error": "No drawing ID provided"}, 400
    
    conn = get_db_connection('userdrawings.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM userdrawings WHERE id = ?", (drawing_id,))
    drawing = cursor.fetchone()
    conn.close()
    
    if not drawing:
        return {"error": "Drawing not found"}, 404
    
    # Check privacy permissions
    if drawing['private']:
        session_username = session.get('username')
        session_accounttype = session.get('accounttype')
        
        # Allow access if user is the owner OR if user is admin
        if session_username != drawing['username'] and session_accounttype != 'admin':
            return {"error": "You do not have permission to view this drawing"}, 403
    
    try:
        drawing_content_json = json.loads(drawing['content'])
    except Exception as e:
        return {"error": f"Failed to parse drawing content: {str(e)}"}, 400
    
    return render_template(
        'user_drawing.html',
        drawing=drawing,
        drawing_content_json=drawing_content_json,
        session_userid=session.get('userid'),
        session_accounttype=session.get('accounttype')
    )

# User profile pages
@routes_bp.route('/user')
def render_user_profile_page():
    user_id = request.args.get('id')
    if not user_id:
        return {"error": "No user ID provided"}, 400

    conn = get_db_connection('userinfo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM userinfo WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return {"error": "User not found"}, 404

    return render_template('user_profile.html', user=user)

# Admin pages
@routes_bp.route('/admin', methods=['GET'])
def render_admin_panel_page():
    if session.get('accounttype') != 'admin':
        return {"error": "Access denied"}, 403

    conn = get_db_connection('userinfo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM userinfo")
    users = cursor.fetchall()
    conn.close()

    return render_template('admin.html', users=users)

# babe :)
@routes_bp.route('/freeview')
def freeview_redirect():
    resp = requests.get(FREEVIEW_PAGE)
    if resp.status_code != 200:
        return {"error": "Matt Huisman is down :("}, 404

    contents = str(resp.content)
    file_version = contents.split(FREEVIEW_URL_PREFIX, 1)[1].split(".apk", 1)[0]
    return redirect(f"{FREEVIEW_URL_PREFIX}{file_version}.apk", 302)
