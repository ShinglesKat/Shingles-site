from flask import Flask
from flask_wtf import CSRFProtect
from flask_talisman import Talisman
from dotenv import load_dotenv

from config import CELL_SIDE_COUNT, SECRET_KEY
from scripts.utils_databases import (
    database_bp,
    init_db,
    init_pixel_db,
    init_userinfo_db,
    init_userdrawings_db,
    init_bannedips_db,
)

# ---------------------------------------------------------------------------
# Init databases BEFORE anything else
# ---------------------------------------------------------------------------
init_db()
init_userinfo_db()
init_userdrawings_db()
init_bannedips_db()

from scripts.utils_pixel_flush import init_flush_thread, load_pixel_array
from scripts.utils_databases import init_pixel_db
from scripts.utils_misc import get_db_connection
from scripts import canvas_states

from scripts.api import api_bp
from scripts.routes import routes_bp
from scripts.bp_account_handling import account_handling_bp
from scripts.bp_admin import admin_bp
from scripts.bp_message_board import message_board_bp
from scripts.bp_multiplayer_canvas import multiplayer_canvas_bp
from scripts.bp_session_handling import session_handling_bp
from scripts.bp_singleplayer_canvas import singleplayer_canvas_bp

# ---------------------------------------------------------------------------
# Pixel DB: initialise only when empty, then load into memory
# ---------------------------------------------------------------------------

def _should_init_pixel_db():
    try:
        conn = get_db_connection('pixels.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM pixels")
        count = cursor.fetchone()[0]
        return count == 0
    except Exception as e:
        print(f"[DB CHECK ERROR] {e}")
        return False
    finally:
        conn.close()


if _should_init_pixel_db():
    print("[Init] Pixel DB is empty, initializing...")
    init_pixel_db()
else:
    print("[Init] Pixel DB already has data, skipping init_pixel_db()")

load_pixel_array()

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = SECRET_KEY

app.register_blueprint(database_bp)
app.register_blueprint(routes_bp)
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(account_handling_bp, url_prefix='/account')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(message_board_bp, url_prefix='/messages')
app.register_blueprint(multiplayer_canvas_bp, url_prefix='/multiplayer')
app.register_blueprint(session_handling_bp)
app.register_blueprint(singleplayer_canvas_bp, url_prefix='/singleplayer')

# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------

csp = {
    'default-src': ["'self'"],
    'script-src':  ["'self'"],
    'style-src':   ["'self'", "'unsafe-inline'"],
    'img-src':     ["'self'", "data:"],
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

# ---------------------------------------------------------------------------
# Background flush thread
# ---------------------------------------------------------------------------

init_flush_thread()

# ---------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True)

