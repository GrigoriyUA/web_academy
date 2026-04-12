# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Homework assignments for the "Vibe Coding" course by Web Academy (Ukrainian). Each lesson folder is an independent project.

---

## Lesson 2 — Flask Calculators

Four themed calculator variants, each is a standalone Flask app.

**Run any calculator:**
```bash
cd "Lesson 2/calculator"        # or calculator-cute / calculator-science / calculator-calories
pip install flask
python app.py
```

Ports: `calculator` → 5000, `calculator-cute` → 5001, `calculator-science` → 5002, `calculator-calories` → 5003. The browser opens automatically on startup.

**Architecture (shared pattern):**
- `app.py` — Flask backend. `POST /calculate` validates input and returns `{"result": ...}` or `{"error": ...}`.  Standard calculators use a character whitelist + `eval()`. The scientific variant also handles trig/log functions and degree/radian mode. The calorie tracker has `/api/search` and `/api/calories` endpoints with a hardcoded food database (~95 items).
- `templates/index.html` — Single-page frontend, vanilla JS `fetch('/calculate')`, unique `<canvas>` animation per variant (binary rain / sparkles / math formulas / food emojis).

---

## Lesson 3 — Telegram Weather Bot

```bash
cd "Lesson 3"
pip install -r requirements.txt
# Put your token in .env: BOT_TOKEN=...
python bot.py
```

**Get a token:** [@BotFather](https://t.me/BotFather) → `/newbot`.

**Architecture:**

| File | Role |
|------|------|
| `bot.py` | Conversation flow: `/start` → city keyboard → date keyboard → forecast. Commands: `/start`, `/help`, `/about`, `/cancel` |
| `weather.py` | Fetches from Open-Meteo API (free, no key). Maps WMO weather codes to Ukrainian descriptions + emoji |
| `cities.py` | Static dict of 24 oblast capitals with lat/lon coordinates |

Conversation has two states (`SELECT_CITY`, `SELECT_DATE`) via `ConversationHandler`. Callback data uses prefixes: `city:CityName` and `date:YYYY-MM-DD`. Forecasts cover 10 days, timezone `Europe/Kyiv`.

**`.env` is gitignored** — never commit the bot token.
