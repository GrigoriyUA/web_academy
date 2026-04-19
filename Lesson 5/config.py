import os
import secrets
import threading

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '').strip()
SECRET_KEY = os.getenv('SECRET_KEY', '').strip() or secrets.token_urlsafe(32)
ADMIN_TELEGRAM_IDS = {
    int(user_id.strip())
    for user_id in os.getenv('ADMIN_TELEGRAM_IDS', '').split(',')
    if user_id.strip().isdigit()
}
DB_PATH = os.getenv('ACCESS_DB_PATH', 'bot_access.db')
ADMIN_PANEL_HOST = os.getenv('ADMIN_PANEL_HOST', '0.0.0.0')
ADMIN_PANEL_PORT = int(os.getenv('ADMIN_PANEL_PORT', '5000'))

if not BOT_TOKEN:
    raise RuntimeError('BOT_TOKEN is missing in .env. Встановіть TELEGRAM_BOT_TOKEN.')

if not ADMIN_PASSWORD:
    raise RuntimeError('ADMIN_PASSWORD is missing in .env. Встановіть ADMIN_PASSWORD.')

db_lock = threading.Lock()
