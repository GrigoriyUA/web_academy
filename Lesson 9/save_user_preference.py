import sqlite3
import json


def save_user_preference(user_id: int, preference: str):
    try:
        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS preferences (
                user_id INTEGER PRIMARY KEY,
                preference TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            INSERT INTO preferences (user_id, preference) 
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET preference=excluded.preference
        ''', (user_id, preference))
        conn.commit()
        conn.close()
        return f"Успішно збережено: {preference}"
    except Exception as e:
        return f"Помилка при збереженні уподобань: {e}"


def save_note(user_id: int, note: str):
    try:
        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                note TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('INSERT INTO notes (user_id, note) VALUES (?, ?)', (user_id, note))
        conn.commit()
        conn.close()
        return f"Нотатку збережено: {note}"
    except Exception as e:
        return f"Помилка при збереженні нотатки: {e}"


def get_user_notes(user_id: int):
    try:
        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                note TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute(
            'SELECT id, note, created_at FROM notes WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        if not rows:
            return "Нотаток не знайдено."
        notes = [{"id": r[0], "note": r[1], "created_at": r[2]} for r in rows]
        return json.dumps(notes, ensure_ascii=False)
    except Exception as e:
        return f"Помилка при отриманні нотаток: {e}"