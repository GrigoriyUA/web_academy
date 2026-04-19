from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from config import BOT_TOKEN, ADMIN_TELEGRAM_IDS, ADMIN_PANEL_PORT
from database import (
    add_or_update_user, get_user_by_telegram_id,
    is_admin_user, is_banned_user, update_user_role_status,
    list_users, log_event,
)


async def require_admin(update: Update) -> bool:
    if not is_admin_user(update.effective_user.id):
        await update.message.reply_text('Ця команда доступна тільки адміністраторам.')
        return False
    return True


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    add_or_update_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        role='admin' if user.id in ADMIN_TELEGRAM_IDS else 'guest',
        status='active'
    )
    if is_banned_user(user.id):
        await update.message.reply_text('Доступ заборонено. Зверніться до адміністратора.')
        return

    role = get_user_by_telegram_id(user.id)['role']
    await update.message.reply_text(
        f'Вітаю, {user.first_name or user.username}!\nВаш рівень доступу: {role}.\n\n'
        'Використайте /help для отримання списку команд.'
    )
    log_event(user.id, 'start', f'role={role}')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if is_banned_user(user.id):
        await update.message.reply_text('Ви заблоковані. Зверніться до адміністратора.')
        return

    role = get_user_by_telegram_id(user.id)['role']
    commands = [
        '/start - Привітання та реєстрація',
        '/help - Список команд',
        '/myrole - Ваш рівень доступу',
        '/request - Запросити повний доступ',
    ]
    if role in ('admin', 'user'):
        commands.append('/status - Перевірити доступ')
    if role == 'admin':
        commands.extend([
            '/adminpanel - Посилання на адміністративну панель',
            '/promote <telegram_id> <role> - Змінити роль користувача',
            '/ban <telegram_id> - Заблокувати користувача',
            '/broadcast <текст> - Розіслати повідомлення',
        ])
    await update.message.reply_text('Доступні команди:\n' + '\n'.join(commands))
    log_event(user.id, 'help', f'role={role}')


async def myrole_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if is_banned_user(user.id):
        await update.message.reply_text('Ваш доступ заблоковано.')
        return
    profile = get_user_by_telegram_id(user.id)
    if not profile:
        await update.message.reply_text('Вас не знайдено в базі. Будь ласка, запустіть /start.')
        return
    await update.message.reply_text(
        f"Ваш Telegram ID: {profile['telegram_id']}\n"
        f"Роль: {profile['role']}\n"
        f"Статус: {profile['status']}"
    )
    log_event(user.id, 'myrole', profile['role'])


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    profile = get_user_by_telegram_id(user.id)
    if not profile:
        await update.message.reply_text('Будь ласка, запустіть /start для реєстрації.')
        return
    await update.message.reply_text(
        f"Ваш статус: {profile['status']}\n"
        f"Роль: {profile['role']}"
    )
    log_event(user.id, 'status', profile['status'])


async def request_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    profile = get_user_by_telegram_id(user.id)
    if profile and profile['role'] in ('admin', 'user'):
        await update.message.reply_text('У вас вже є доступ до сервісу.')
        return
    add_or_update_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        role='guest',
        status='pending'
    )
    await update.message.reply_text(
        'Запит на доступ відправлено. Адміністратор перевірить ваш запит протягом найближчого часу.'
    )
    log_event(user.id, 'request', 'requested access')
    admin_message = (
        f'📌 Новий запит на доступ:\n'
        f'User: {user.first_name or user.username} ({user.id})\n'
        f'Telegram: @{user.username if user.username else "не вказано"}\n'
        f'Перейдіть в адмін-панель для підтвердження.'
    )
    for admin_id in ADMIN_TELEGRAM_IDS:
        await context.bot.send_message(chat_id=admin_id, text=admin_message)


async def adminpanel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_admin(update):
        return
    user = update.effective_user
    panel_url = f'http://localhost:{ADMIN_PANEL_PORT}/admin'
    await update.message.reply_text(
        f'Адмін-панель запущена за адресою: {panel_url}\n'
        'Використайте пароль з файлу .env для входу.'
    )
    log_event(user.id, 'adminpanel', 'requested admin panel link')


async def promote_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_admin(update):
        return
    user = update.effective_user
    args = context.args
    if len(args) != 2 or args[1] not in ('guest', 'user', 'admin'):
        await update.message.reply_text('Використання: /promote <telegram_id> <guest|user|admin>')
        return
    target_id = int(args[0]) if args[0].isdigit() else None
    if target_id is None:
        await update.message.reply_text('Невірний Telegram ID.')
        return
    if not update_user_role_status(target_id, args[1], 'active'):
        await update.message.reply_text('Користувача не знайдено. Нехай надішле /start.')
        return
    await update.message.reply_text(f'Роль користувача {target_id} змінено на {args[1]}.')
    log_event(user.id, 'promote', f'target={target_id} role={args[1]}')


async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_admin(update):
        return
    user = update.effective_user
    args = context.args
    if len(args) != 1:
        await update.message.reply_text('Використання: /ban <telegram_id>')
        return
    target_id = int(args[0]) if args[0].isdigit() else None
    if target_id is None:
        await update.message.reply_text('Невірний Telegram ID.')
        return
    if not update_user_role_status(target_id, 'guest', 'banned'):
        await update.message.reply_text('Користувача не знайдено. Нехай надішле /start.')
        return
    await update.message.reply_text(f'Користувача {target_id} заблоковано.')
    log_event(user.id, 'ban', f'target={target_id}')


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_admin(update):
        return
    user = update.effective_user
    text = ' '.join(context.args).strip()
    if not text:
        await update.message.reply_text('Використання: /broadcast <повідомлення>')
        return
    users = list_users()
    count = 0
    for profile in users:
        if profile['status'] == 'active' and profile['role'] != 'banned':
            try:
                await context.bot.send_message(chat_id=profile['telegram_id'], text=f'📢 Адміністрація: {text}')
                count += 1
            except Exception:
                pass
    await update.message.reply_text(f'Повідомлення надіслано {count} користувачам.')
    log_event(user.id, 'broadcast', f'count={count}')


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if is_banned_user(user.id):
        await update.message.reply_text('Ваш доступ заблоковано.')
        return
    await update.message.reply_text(
        'Я розумію лише команди. Скористайтеся /help для списку доступних команд.'
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f'Error: {context.error}')
    if isinstance(update, Update) and update.message:
        await update.message.reply_text('Виникла помилка. Спробуйте ще раз пізніше.')


def build_bot_application() -> Application:
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('myrole', myrole_command))
    application.add_handler(CommandHandler('status', status_command))
    application.add_handler(CommandHandler('request', request_command))
    application.add_handler(CommandHandler('adminpanel', adminpanel_command))
    application.add_handler(CommandHandler('promote', promote_command))
    application.add_handler(CommandHandler('ban', ban_command))
    application.add_handler(CommandHandler('broadcast', broadcast_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    application.add_error_handler(error_handler)
    return application
