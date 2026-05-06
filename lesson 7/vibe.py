import asyncio
from datetime import date

from groq import Groq

from weather import get_forecast

VIBE_STYLES = {
    "shakespeare": ("🎭 Шекспір",  "у стилі Вільяма Шекспіра — поетично, з драмою і метафорами"),
    "robot":       ("🤖 Робот",    "як технічний звіт робота — сухо, з числами і логікою, без емоцій"),
    "yogi":        ("🧘 Йог",      "як мудрець-йог — філософськи, спокійно, з духовними метафорами"),
    "reporter":    ("📰 Репортер", "як терміновий репортаж у прямому ефірі — схвильовано і динамічно"),
    "standup":     ("😂 Стендап",  "як стендап-комедіант — з гумором, жартами і несподіваними порівняннями"),
}

_SYSTEM_PROMPT = """\
Ти — ВайбМетеоролог. Твоя задача: отримати погоду через інструмент get_weather, а потім написати короткий ТВОРЧИЙ текст про неї.

СТИЛЬ: {style}

ВАЖЛИВО: Ти не звітуєш про погоду — ти розповідаєш про неї у заданому стилі. \
Використовуй метафори, образи, емоції. Вплітай реальні цифри (температуру, вітер) органічно в текст.

Мова: ТІЛЬКИ українська. Обсяг: 3-5 речень.\
"""

_TOOL_SCHEMA = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Отримати прогноз погоди на сьогодні для міста України",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "Назва міста українською (наприклад: Київ)"},
            },
            "required": ["city"],
        },
    },
}]


def _get_weather(city: str) -> dict:
    result = get_forecast(city, date.today().isoformat())
    return result if result is not None else {"error": f"Немає даних для міста {city}"}


def run_vibe_agent(city: str, style: str, api_key: str) -> str:
    client = Groq(api_key=api_key)

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT.format(style=style)},
        {"role": "user", "content": f"Місто: {city}. Отримай погоду і напиши про неї у заданому стилі — творчо, не як список фактів."},
    ]

    # Крок 1: модель вирішує які інструменти викликати
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        tools=_TOOL_SCHEMA,
        tool_choice="auto",
    )
    msg = response.choices[0].message

    # Крок 2: виконуємо tool calls і відправляємо результати назад
    if msg.tool_calls:
        messages.append(msg)
        for call in msg.tool_calls:
            result = _get_weather(city)  # завжди використовуємо оригінальну назву від користувача
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": str(result),
            })

        # Крок 3: модель формує фінальну відповідь на основі даних погоди
        final = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
        )
        return final.choices[0].message.content

    return msg.content or "Не вдалося отримати відповідь."


async def run_vibe_agent_async(city: str, style: str, api_key: str) -> str:
    return await asyncio.to_thread(run_vibe_agent, city, style, api_key)
