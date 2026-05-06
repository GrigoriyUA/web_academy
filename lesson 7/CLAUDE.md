# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the bot

```bash
pip install -r requirements.txt
python bot.py
```

Токен бота зберігається у файлі `.env`:
```
BOT_TOKEN=your_token_here
```

Отримати токен: [@BotFather](https://t.me/BotFather) → `/newbot`.

## Architecture

**`cities.py`** — статичний словник 24 обласних центрів України з координатами (lat/lon). Використовується в `weather.py` для формування запиту до API.

**`weather.py`** — запити до [Open-Meteo API](https://open-meteo.com/) (безкоштовно, без ключа). Функція `get_forecast(city_name, date_str)` повертає dict з полями `temp_max`, `temp_min`, `precipitation`, `wind_speed`, `description`, `icon`. WMO-коди погоди маппуються на українські описи та emoji.

**`bot.py`** — Telegram-бот на `python-telegram-bot` v22. Conversation flow:

```
/start → вибір міста (SELECT_CITY) → вибір дати (SELECT_DATE) → прогноз
```

- Callback data: `city:НазваМіста` і `date:YYYY-MM-DD`
- Inline-клавіатура міст: 3 в рядку, алфавітно
- Inline-клавіатура дат: 2 в рядку, 10 днів наперед
- Команди: `/start`, `/help`, `/about`, `/cancel`, `/vibe`
- `/help` і `/about` працюють у будь-якому стані через `fallbacks`

**`vibe.py`** — команда `/vibe` з Gemini Agent Mode:
- `VIBE_STYLES` — 5 вбудованих стилів (Шекспір, Робот, Йог, Репортер, Стендап) + "Свій стиль"
- `get_weather(city)` — інструмент для агента, викликає `get_forecast` на сьогоднішню дату
- `run_vibe_agent(city, style, api_key)` — запускає Gemini 2.0 Flash з `automatic_function_calling`; модель сама вирішує коли викликати `get_weather`
- `run_vibe_agent_async` — обгортка через `asyncio.to_thread` для async-хендлерів бота

Flow `/vibe`:
```
/vibe → вибір стилю (кнопки або текст) → вибір міста → агент → прогноз у стилі
```

Потрібна змінна середовища: `GEMINI_API_KEY` (отримати на aistudio.google.com, безкоштовно)
