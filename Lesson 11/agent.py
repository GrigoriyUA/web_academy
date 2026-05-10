import os
import sys
import uuid
import datetime
import json
import requests
import structlog
from groq import Groq, APIConnectionError, APITimeoutError, RateLimitError
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryCallState,
)

from logging_config import setup_logging

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

_LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.log")
setup_logging(log_file=_LOG_FILE)

log = structlog.get_logger()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def _log_retry(retry_state: RetryCallState) -> None:
    log.warning(
        "llm_retry",
        attempt=retry_state.attempt_number,
        wait_seconds=round(retry_state.next_action.sleep, 2),
        error=str(retry_state.outcome.exception()),
        exc_type=type(retry_state.outcome.exception()).__name__,
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((APIConnectionError, APITimeoutError, RateLimitError)),
    before_sleep=_log_retry,
    reraise=True,
)
def _call_llm(messages: list, tools: list):
    return client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )


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
        log.debug("calculate_done", expresion=expresion, result=result)
        return f"Результат: {result}"
    except Exception as e:
        log.warning("calculate_error", expresion=expresion, error=str(e))
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
    log.info("note_saved", content_preview=content[:60])
    return "Нотатку успішно збережено."


def set_reminder(task: str, time: str) -> str:
    log.info("reminder_set", task=task, time=time)
    return f"Окей, я нагадаю тобі: '{task}' {time}."


def get_top_songs(limit: int = 10) -> str:
    try:
        url = f"https://itunes.apple.com/ua/rss/topsongs/limit={limit}/json"
        data = requests.get(url, timeout=10).json()
        entries = data["feed"]["entry"]
        lines = [
            f"{i+1}. {e['im:name']['label']} — {e['im:artist']['label']}"
            for i, e in enumerate(entries)
        ]
        log.info("top_songs_fetched", count=len(lines))
        return "\n".join(lines)
    except Exception as e:
        log.error("top_songs_error", error=str(e))
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
        log.info("new_movies_fetched", count=len(lines))
        return "\n".join(lines)
    except Exception as e:
        log.error("new_movies_error", error=str(e))
        return f"Помилка отримання фільмів: {e}"


def get_exchange_rate(currency: str = "USD") -> str:
    try:
        url = f"https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode={currency}&json"
        data = requests.get(url, timeout=10).json()
        if not data:
            log.warning("exchange_rate_not_found", currency=currency)
            return f"Курс для валюти {currency} не знайдено."
        rate = data[0]["rate"]
        date = data[0].get("exchangedate", "")
        log.info("exchange_rate_fetched", currency=currency, rate=rate, date=date)
        return f"Курс {currency} до UAH на {date}: {rate}"
    except Exception as e:
        log.error("exchange_rate_error", currency=currency, error=str(e))
        return f"Помилка отримання курсу: {e}"


def run_agent(user_prompt: str) -> str:
    request_id = str(uuid.uuid4())[:8]
    structlog.contextvars.bind_contextvars(request_id=request_id)

    log.info("prompt_received", prompt=user_prompt)

    available_functions = {
        "calculate": calculate,
        "save_note": save_note,
        "set_reminder": set_reminder,
        "get_exchange_rate": get_exchange_rate,
        "get_top_songs": get_top_songs,
        "get_new_movies": get_new_movies,
    }

    try:
        log.info("llm_call_start", model="llama-3.3-70b-versatile")
        response = _call_llm(
            messages=[{"role": "user", "content": user_prompt}],
            tools=tools,
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if tool_calls:
            log.info("tools_selected", count=len(tool_calls))

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                log.info("tool_called", tool=function_name, args=function_args)

                function_to_call = available_functions[function_name]
                result = function_to_call(**function_args)

                log.info("tool_result", tool=function_name, result=result[:120])

            return "Завдання виконано! Перевір нотатки та нагадування."
        else:
            answer = response_message.content
            log.info("direct_answer", length=len(answer))
            return answer

    except Exception as e:
        log.error("agent_error", error=str(e))
        raise
    finally:
        structlog.contextvars.clear_contextvars()


if __name__ == "__main__":
    prompt = "Запиши нотатку: сьогодні чудовий день, все вдалось!"
    result = run_agent(prompt)
    log.info("agent_done", result=result)
