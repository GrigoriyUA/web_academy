# Telegram Weather Bot — Прогноз погоди для України

Telegram-бот, який надає прогноз погоди для всіх 24 обласних центрів України на до 10 днів наперед.

## Можливості

- Вибір міста з інтерактивного меню (24 обласних центри)
- Вибір дати (сьогодні + 9 днів наперед)
- Прогноз: температура, опади, вітер, опис погоди
- Безкоштовне погодне API без реєстрації

---

## Встановлення та запуск

### 1. Клонуй репозиторій

```bash
git clone https://github.com/GrigoriyUA/web_academy.git
cd web_academy/Lesson\ 3
```

### 2. Встанови залежності

```bash
pip install -r requirements.txt
```

### 3. Отримай токен бота

1. Відкрий Telegram і знайди [@BotFather](https://t.me/BotFather)
2. Надішли команду `/newbot`
3. Введи ім'я та username бота
4. Скопіюй отриманий токен

### 4. Створи файл `.env`

У папці `Lesson 3` створи файл `.env` та встав свій токен:

```
BOT_TOKEN=ваш_токен_тут
```

### 5. Запусти бота

```bash
python bot.py
```

---

## Використання

| Команда | Опис |
|---------|------|
| `/start` | Розпочати новий запит прогнозу |
| `/help` | Список команд та інструкція |
| `/about` | Інформація про бота |
| `/cancel` | Скасувати поточний запит |

---

## Технології

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) — бібліотека для Telegram Bot API
- [Open-Meteo](https://open-meteo.com/) — безкоштовний погодний API (без реєстрації)
- [python-dotenv](https://github.com/theskumar/python-dotenv) — завантаження змінних середовища
