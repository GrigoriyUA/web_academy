import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List

from config import DB_PATH, db_lock, ADMIN_TELEGRAM_IDS

CREATE_USERS_TABLE = '''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    role TEXT NOT NULL DEFAULT 'guest',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
'''

CREATE_ACCESS_LOG_TABLE = '''
CREATE TABLE IF NOT EXISTS access_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    event TEXT NOT NULL,
    details TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
'''


def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_cursor():
    with db_lock:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        finally:
            conn.close()


def init_db() -> None:
    with db_cursor() as cursor:
        cursor.execute(CREATE_USERS_TABLE)
        cursor.execute(CREATE_ACCESS_LOG_TABLE)

    for telegram_id in ADMIN_TELEGRAM_IDS:
        add_or_update_user(telegram_id=telegram_id, username='admin', role='admin', status='active')


def add_or_update_user(telegram_id: int, username: str | None = None, first_name: str | None = None,
                       last_name: str | None = None, role: str = 'guest', status: str = 'active') -> None:
    with db_cursor() as cursor:
        now = datetime.utcnow().isoformat(sep=' ', timespec='seconds')
        cursor.execute('SELECT role, status FROM users WHERE telegram_id = ?', (telegram_id,))
        row = cursor.fetchone()
        if row is None:
            cursor.execute(
                'INSERT INTO users (telegram_id, username, first_name, last_name, role, status, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (telegram_id, username, first_name, last_name, role, status, now)
            )
        else:
            if telegram_id in ADMIN_TELEGRAM_IDS:
                role = 'admin'
                status = 'active'
            cursor.execute(
                'UPDATE users SET username = ?, first_name = ?, last_name = ?, role = ?, status = ?, updated_at = ? WHERE telegram_id = ?',
                (username, first_name, last_name, role, status, now, telegram_id)
            )


def get_user_by_telegram_id(telegram_id: int) -> dict | None:
    with db_cursor() as cursor:
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        row = cursor.fetchone()
    return dict(row) if row else None


def update_user_role_status(telegram_id: int, role: str, status: str) -> bool:
    with db_cursor() as cursor:
        cursor.execute('UPDATE users SET role = ?, status = ?, updated_at = ? WHERE telegram_id = ?',
                       (role, status, datetime.utcnow().isoformat(sep=' ', timespec='seconds'), telegram_id))
        rowcount = cursor.rowcount
    return rowcount > 0


def remove_user(telegram_id: int) -> bool:
    with db_cursor() as cursor:
        cursor.execute('DELETE FROM users WHERE telegram_id = ?', (telegram_id,))
        rowcount = cursor.rowcount
    return rowcount > 0


def list_users() -> List[Dict]:
    with db_cursor() as cursor:
        cursor.execute('SELECT * FROM users ORDER BY updated_at DESC')
        rows = cursor.fetchall()
    return [dict(row) for row in rows]


def log_event(telegram_id: int, event: str, details: str | None = None) -> None:
    with db_cursor() as cursor:
        cursor.execute(
            'INSERT INTO access_logs (telegram_id, event, details) VALUES (?, ?, ?)',
            (telegram_id, event, details)
        )


def user_has_access(telegram_id: int) -> bool:
    user = get_user_by_telegram_id(telegram_id)
    return bool(user and user['status'] == 'active' and user['role'] != 'banned')


def is_admin_user(telegram_id: int) -> bool:
    user = get_user_by_telegram_id(telegram_id)
    return bool(user and user['role'] == 'admin' and user['status'] == 'active')


def is_banned_user(telegram_id: int) -> bool:
    user = get_user_by_telegram_id(telegram_id)
    return bool(user and user['status'] == 'banned')
