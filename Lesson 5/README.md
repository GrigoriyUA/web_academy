# Lesson 5 — Telegram Access Bot

Telegram-бот з системою ролей та Flask-адмін-панеллю.

## Структура

```
Lesson 5/
├── config.py          # Конфігурація (.env змінні)
├── database.py        # SQLite: підключення, запити, хелпери
├── handlers.py        # Telegram команди
├── admin.py           # Flask адмін-панель
├── main.py            # Точка входу
└── templates/
    ├── login.html     # Сторінка входу
    └── admin.html     # Панель управління
```

## Налаштування

1. Створи `.env` файл:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
ADMIN_PASSWORD=your_password
SECRET_KEY=your_secret_key
ADMIN_TELEGRAM_IDS=123456789
ACCESS_DB_PATH=bot_access.db
ADMIN_PANEL_HOST=0.0.0.0
ADMIN_PANEL_PORT=5000
```

2. Встанови залежності:

```bash
pip install python-telegram-bot flask python-dotenv
```

3. Запусти:

```bash
python main.py
```

Бот запуститься, адмін-панель буде доступна на `http://localhost:5000/admin`.

## Ролі користувачів

| Роль | Можливості |
|------|-----------|
| `guest` | `/start`, `/help`, `/myrole`, `/request` |
| `user` | + `/status` |
| `admin` | + `/adminpanel`, `/promote`, `/ban`, `/broadcast` |

## Команди адміна

- `/promote <telegram_id> <guest|user|admin>` — змінити роль
- `/ban <telegram_id>` — заблокувати користувача
- `/broadcast <текст>` — розіслати повідомлення всім активним користувачам
