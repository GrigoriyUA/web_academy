import threading

from config import ADMIN_PANEL_HOST, ADMIN_PANEL_PORT
from database import init_db
from handlers import build_bot_application
from admin import run_admin_panel


def main() -> None:
    init_db()
    threading.Thread(target=run_admin_panel, daemon=True).start()
    application = build_bot_application()
    print(f'Запуск адмін-панелі: http://{ADMIN_PANEL_HOST}:{ADMIN_PANEL_PORT}/admin')
    print('Запуск Telegram бота...')
    application.run_polling()


if __name__ == '__main__':
    main()
