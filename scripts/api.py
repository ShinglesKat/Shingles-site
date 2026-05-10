from flask import Blueprint

api_bp = Blueprint('api_bp', __name__)

# API routes are registered on the individual feature blueprints
# (bp_multiplayer_canvas, bp_singleplayer_canvas, etc.) under their own
# url_prefix.  This module exists so backend.py has a single api_bp to mount
# at /api for any shared/catch-all API endpoints added in future.
