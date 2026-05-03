import os
import sqlite3
import json
from datetime import date, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'reporting.db')


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS preferences (
            user_id INTEGER NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            PRIMARY KEY (user_id, key)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    conn.commit()
    return conn


def save_user_preference(user_id: int, preference: str) -> str:
    try:
        conn = _get_conn()
        conn.execute('''
            INSERT INTO preferences (user_id, key, value)
            VALUES (?, 'preference', ?)
            ON CONFLICT(user_id, key) DO UPDATE SET value=excluded.value
        ''', (user_id, preference))
        conn.commit()
        conn.close()
        return f"Уподобання збережено: {preference}"
    except Exception as e:
        return f"Помилка: {e}"


def add_expense(user_id: int, amount: float, category: str, expense_date: str = None) -> str:
    try:
        conn = _get_conn()
        if expense_date is None:
            expense_date = date.today().isoformat()
        conn.execute(
            'INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)',
            (user_id, amount, category, expense_date)
        )
        conn.commit()
        conn.close()
        return f"Витрату {amount} грн у категорії '{category}' за {expense_date} збережено."
    except Exception as e:
        return f"Помилка: {e}"


def get_spending_stats(user_id: int, category: str, period: str = "month") -> str:
    try:
        conn = _get_conn()
        today = date.today()
        if period == "month":
            date_filter = today.strftime("%Y-%m")
            cursor = conn.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id=? AND category=? AND date LIKE ?",
                (user_id, category, f"{date_filter}%")
            )
        elif period == "week":
            week_ago = (today - timedelta(days=7)).isoformat()
            cursor = conn.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id=? AND category=? AND date >= ?",
                (user_id, category, week_ago)
            )
        elif period == "year":
            year_filter = today.strftime("%Y")
            cursor = conn.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id=? AND category=? AND date LIKE ?",
                (user_id, category, f"{year_filter}%")
            )
        else:
            conn.close()
            return json.dumps({"error": f"Невідомий period: {period}"})
        total = cursor.fetchone()[0]
        conn.close()
        return json.dumps({"category": category, "period": period, "total": total}, ensure_ascii=False)
    except Exception as e:
        return f"Помилка: {e}"
