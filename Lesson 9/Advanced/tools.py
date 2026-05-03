import os
import sqlite3
import json

DB_PATH = os.path.join(os.path.dirname(__file__), 'proactive_memory.db')


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            preference TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn


def save_user_preference(user_id: int, preference: str) -> str:
    try:
        conn = _get_conn()
        conn.execute(
            'INSERT INTO preferences (user_id, preference) VALUES (?, ?)',
            (user_id, preference)
        )
        conn.commit()
        conn.close()
        return f"Уподобання збережено: {preference}"
    except Exception as e:
        return f"Помилка: {e}"


def search_user_history(user_id: int, query: str) -> str:
    try:
        conn = _get_conn()
        keywords = [w.strip() for w in query.lower().split() if len(w.strip()) > 2]
        if not keywords:
            conn.close()
            return json.dumps({"results": []}, ensure_ascii=False)

        placeholders = " OR ".join(["LOWER(preference) LIKE ?" for _ in keywords])
        params = [f"%{kw}%" for kw in keywords] + [user_id]
        cursor = conn.execute(
            f"SELECT preference, created_at FROM preferences WHERE ({placeholders}) AND user_id=? ORDER BY created_at DESC",
            params
        )
        rows = cursor.fetchall()
        conn.close()
        results = [{"preference": r[0], "saved_at": r[1]} for r in rows]
        return json.dumps({"results": results}, ensure_ascii=False)
    except Exception as e:
        return f"Помилка: {e}"
