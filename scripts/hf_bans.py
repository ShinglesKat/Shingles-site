import datetime
from flask import jsonify, request
from scripts.hf_misc import get_db_connection

def get_user_ip():
    if request.environ.get('HTTP_X_FORWARDED_FOR'):
        return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()
    elif request.environ.get('HTTP_X_REAL_IP'):
        return request.environ.get('HTTP_X_REAL_IP')
    else:
        return request.environ.get('REMOTE_ADDR', 'unknown')

def check_if_banned(ip_address):
    try:
        conn = get_db_connection('bannedips.db')
        cursor = conn.cursor()
        current_time = datetime.now(datetime.timezone.utc)
        current_iso = current_time.isoformat()
        cursor.execute("""
            SELECT reason, ban_expires_at, ban_duration 
            FROM bannedIPs 
            WHERE ip = ? AND ban_expires_at > ?
        """, (ip_address, current_iso))
        ban_record = cursor.fetchone()
        if ban_record:
            reason, expires_at, duration = ban_record
            return True, {
                'banned': True,
                'reason': reason,
                'expires_at': expires_at,
                'ban_duration': duration
            }
        else:
            return False, None
    except Exception as e:
        print(f"[BAN CHECK ERROR] {e}")
        return False, None
    finally:
        conn.close()

def handle_ban_check(custom_message):
    user_ip = get_user_ip()
    is_banned, ban_info = check_if_banned(user_ip)
    if is_banned:
        error_message = custom_message
        if ban_info.get('reason'):
            error_message += f" Reason: {ban_info['reason']}"
        if ban_info.get('expires_at'):
            try:
                expires_dt = datetime.fromisoformat(ban_info['expires_at'].replace('Z', '+00:00'))
                error_message += f" Ban expires: {expires_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            except Exception:
                error_message += f" Ban expires: {ban_info['expires_at']}"
        return jsonify({'error': error_message}), 403
    return None