"""
utils_pixel_flush.py
Owns the in-memory pixel state, the background flush thread, and the graceful
shutdown hook.  Import this module once at startup (backend.py already does so
via load_pixels_from_db / init_flush_thread) — everything else just touches
canvas_states directly.
"""
import atexit
import sqlite3
import time
from threading import Thread

from config import CELL_SIDE_COUNT, SAVE_INTERVAL
from scripts import canvas_states
from scripts.config import DEFAULT_COLOUR
from scripts.utils_misc import get_db_connection

# ---------------------------------------------------------------------------
# Pixel array loader
# ---------------------------------------------------------------------------

def load_pixel_array():
    """Populate canvas_states.pixelArray from the database."""
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
        canvas_states.pixelArray[:] = arr
        print(f"[Startup] Loaded pixel array ({CELL_SIDE_COUNT}x{CELL_SIDE_COUNT})")
    except sqlite3.Error as e:
        print(f"[Startup ERROR] Failed to load pixel array: {e}")
        canvas_states.pixelArray[:] = arr  # safe fallback
    return canvas_states.pixelArray


# ---------------------------------------------------------------------------
# Flush helpers
# ---------------------------------------------------------------------------

def flush_pending_updates():
    """Write all pending pixel updates to the database in one batch."""
    if not canvas_states.pendingUpdates:
        print("[Flush] No pending updates.")
        return

    updates = canvas_states.pendingUpdates[:]
    canvas_states.pendingUpdates.clear()

    conn = None
    try:
        conn = get_db_connection('pixels.db')
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT OR REPLACE INTO pixels (x, y, colour, ip_address)
            VALUES (?, ?, ?, ?)
            """,
            [(u['x'], u['y'], u['colour'], u.get('ip_address')) for u in updates],
        )
        conn.commit()
        print(f"[Flush] Saved {len(updates)} pixel(s).")
    except sqlite3.Error as e:
        print(f"[Flush ERROR] Database error: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"[Flush ERROR] Unexpected error: {e}")
    finally:
        if conn:
            conn.close()


# ---------------------------------------------------------------------------
# Background flush thread
# ---------------------------------------------------------------------------

_stop_thread = False
_flush_thread: Thread | None = None


def _background_flush_loop():
    global _stop_thread
    print(f"[Startup] Flush thread running (interval: {SAVE_INTERVAL}s).")
    while not _stop_thread:
        # Sleep in small increments so we can respond to stop signals quickly.
        for _ in range(SAVE_INTERVAL):
            if _stop_thread:
                break
            time.sleep(1)
        if not _stop_thread:
            flush_pending_updates()
    print("[Shutdown] Flush thread stopped.")


def _graceful_shutdown():
    global _stop_thread
    print("[Shutdown] Forcing final pixel flush...")
    _stop_thread = True
    if _flush_thread and _flush_thread.is_alive():
        _flush_thread.join(timeout=5)
    flush_pending_updates()
    print("[Shutdown] Final flush complete.")


def init_flush_thread():
    global _flush_thread, _stop_thread
    if _flush_thread is not None and _flush_thread.is_alive():
        print("[Startup] Flush thread already running, skipping.")
        return
    _stop_thread = False
    _flush_thread = Thread(target=_background_flush_loop, daemon=True)
    _flush_thread.start()
    atexit.register(_graceful_shutdown)
    print("[Startup] Background flush thread started.")
