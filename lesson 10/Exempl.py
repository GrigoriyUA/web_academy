import os
import sys
import datetime
import json
import requests
from groq import Groq
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Обчислює математичний вираз",
            "parameters": {
                "type": "object",
                "properties": {
                    "expresion": {"type": "string", "description": "Математичний вираз, наприклад '100 * 0.05'"}
                },
                "required": ["expresion"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_note",
            "description": "Зберігає нотатку у файл",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Текст нотатки"}
                },
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_reminder",
            "description": "Встановлює нагадування",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Що нагадати"},
                    "time": {"type": "string", "description": "Коли нагадати"},
                },
                "required": ["task", "time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_exchange_rate",
            "description": "Отримує курс валюти до UAH з НБУ",
            "parameters": {
                "type": "object",
                "properties": {
                    "currency": {"type": "string", "description": "Код валюти, наприклад 'USD'"}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_songs",
            "description": "Повертає список найпопулярніших пісень прямо зараз",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Кількість пісень (за замовчуванням 10)"}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_new_movies",
            "description": "Повертає список нових фільмів що нещодавно вийшли",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Кількість фільмів (за замовчуванням 10)"}
                },
                "required": [],
            },
        },
    },
]


def calculate(expresion: str) -> str:
    try:
        result = eval(expresion, {"__builtins__": None}, {})
        return f"Результат: {result}"
    except Exception as e:
        return f"Помилка: {e}"


def _mood_emoji(text: str) -> str:
    t = text.lower()
    if any(kw in t for kw in ["сумн", "горе", "тяжк", "погано", "невдач", "проблем", "страшн", "боюс", "стрес"]):
        return "😢"
    if any(kw in t for kw in ["терміново", "важливо", "дедлайн", "горить", "негайно", "увага", "зустріч"]):
        return "⚡"
    if any(kw in t for kw in ["радіс", "щасли", "чудов", "весел", "люблю", "перемог", "успіх", "вдяч", "ура"]):
        return "😊"
    return "📝"


def save_note(content: str) -> str:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    emoji = _mood_emoji(content)
    with open("notes.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {emoji} {content}\n")
    return "Нотатку успішно збережено."


def set_reminder(task: str, time: str) -> str:
    return f"Окей, я нагадаю тобі: '{task}' {time}."


def get_weather(city: str) -> str:
    pass


def get_top_songs(limit: int = 10) -> str:
    try:
        url = f"https://itunes.apple.com/ua/rss/topsongs/limit={limit}/json"
        data = requests.get(url, timeout=10).json()
        entries = data["feed"]["entry"]
        lines = [
            f"{i+1}. {e['im:name']['label']} — {e['im:artist']['label']}"
            for i, e in enumerate(entries)
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Помилка отримання пісень: {e}"


def get_new_movies(limit: int = 10) -> str:
    try:
        url = f"https://itunes.apple.com/ua/rss/topmovies/limit={limit}/json"
        data = requests.get(url, timeout=10).json()
        entries = data["feed"]["entry"]
        lines = [
            f"{i+1}. {e['im:name']['label']} ({e['im:releaseDate']['attributes']['label']})"
            for i, e in enumerate(entries)
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Помилка отримання фільмів: {e}"


def get_exchange_rate(currency: str = "USD") -> str:
    try:
        url = f"https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode={currency}&json"
        response = requests.get(url, timeout=10)
        data = response.json()
        if not data:
            return f"Курс для валюти {currency} не знайдено."
        rate = data[0]["rate"]
        date = data[0].get("exchangedate", "")
        return f"Курс {currency} до UAH на {date}: {rate}"
    except Exception as e:
        return f"Помилка отримання курсу: {e}"


def run_wiper_agent(user_prompt):
    available_functions = {
        "calculate": calculate,
        "save_note": save_note,
        "set_reminder": set_reminder,
        "get_exchange_rate": get_exchange_rate,
        "get_top_songs": get_top_songs,
        "get_new_movies": get_new_movies,
    }

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": user_prompt}],
        tools=tools,
        tool_choice="auto",
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    if tool_calls:
        print(f"--- Бот вирішив використати {len(tool_calls)} інструментів ---")
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(**function_args)
            print(f"Виклик {function_name} з аргументами {function_args}")
            print(f"Результат: {function_response}")
        return "Завдання виконано! Перевір нотатки та нагадування."
    else:
        return response_message.content


if __name__ == "__main__":
    # тест нотаток з настроєм
    promt = "Запиши нотатку: сьогодні чудовий день, все вдалось!"
    print(run_wiper_agent(promt))


