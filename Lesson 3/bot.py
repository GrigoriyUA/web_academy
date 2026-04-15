import logging
from datetime import date, timedelta

from pydantic_settings import BaseSettings
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)

from cities import CITIES
from weather import get_forecast


class Settings(BaseSettings):
    bot_token: str

    model_config = {"env_file": ".env"}


settings = Settings()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

SELECT_CITY, SELECT_DATE = range(2)

UA_WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
UA_MONTHS = [
    "", "січня", "лютого", "березня", "квітня", "травня", "червня",
    "липня", "серпня", "вересня", "жовтня", "листопада", "грудня",
]
UA_WEEKDAYS_FULL = ["понеділок", "вівторок", "середу", "четвер", "п'ятницю", "суботу", "неділю"]


def _city_keyboard() -> InlineKeyboardMarkup:
    cities = sorted(CITIES.keys())
    rows = []
    for i in range(0, len(cities), 3):
        row = [InlineKeyboardButton(c, callback_data=f"city:{c}") for c in cities[i:i+3]]
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def _date_keyboard() -> InlineKeyboardMarkup:
    today = date.today()
    rows = []
    dates = [today + timedelta(days=i) for i in range(10)]
    for i in range(0, len(dates), 2):
        row = []
        for d in dates[i:i+2]:
            label = f"{d.day:02d}.{d.month:02d} ({UA_WEEKDAYS[d.weekday()]})"
            row.append(InlineKeyboardButton(label, callback_data=f"date:{d.isoformat()}"))
        rows.append(row)
    return InlineKeyboardMarkup(rows)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Привіт! Я бот прогнозу погоди для обласних центрів України.\n\n"
        "Оберіть місто:",
        reply_markup=_city_keyboard(),
    )
    return SELECT_CITY


async def city_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    city = query.data.split(":", 1)[1]
    context.user_data["city"] = city

    await query.edit_message_text(
        f"Місто: {city}\n\nОберіть дату:",
        reply_markup=_date_keyboard(),
    )
    return SELECT_DATE


async def date_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    date_str = query.data.split(":", 1)[1]
    city = context.user_data.get("city", "")

    forecast = get_forecast(city, date_str)

    if forecast is None:
        await query.edit_message_text(
            "Не вдалося отримати прогноз. Спробуйте ще раз — /start"
        )
        return ConversationHandler.END

    d = date.fromisoformat(date_str)
    date_label = (
        f"{d.day} {UA_MONTHS[d.month]} {d.year} р. "
        f"({UA_WEEKDAYS_FULL[d.weekday()]})"
    )

    sign_max = "+" if forecast["temp_max"] >= 0 else ""
    sign_min = "+" if forecast["temp_min"] >= 0 else ""

    text = (
        f"{forecast['icon']} Прогноз погоди: {city}\n"
        f"📅 {date_label}\n\n"
        f"🌡 Температура: від {sign_min}{forecast['temp_min']}°C до {sign_max}{forecast['temp_max']}°C\n"
        f"🌧 Опади: {forecast['precipitation']:.1f} мм\n"
        f"💨 Вітер: до {forecast['wind_speed']} км/год\n"
        f"☁️ Умови: {forecast['description']}\n\n"
        f"🔄 /start — новий запит"
    )

    await query.edit_message_text(text)
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Доступні команди:\n\n"
        "/start — розпочати новий запит прогнозу погоди\n"
        "/help — показати цю довідку\n"
        "/about — інформація про бота\n"
        "/cancel — скасувати поточний запит\n\n"
        "Як користуватись:\n"
        "1. Введіть /start\n"
        "2. Оберіть обласний центр із списку\n"
        "3. Оберіть дату (до 10 днів наперед)\n"
        "4. Отримайте прогноз погоди"
    )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Бот прогнозу погоди для України\n\n"
        "Надає прогноз для всіх 24 обласних центрів на до 10 днів наперед.\n\n"
        "Дані: Open-Meteo (open-meteo.com) — безкоштовний погодний сервіс.\n"
        "Часовий пояс: Київ (UTC+2/+3)"
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Скасовано. Введіть /start для нового запиту.")
    return ConversationHandler.END


def main() -> None:
    app = Application.builder().token(settings.bot_token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_CITY: [CallbackQueryHandler(city_selected, pattern=r"^city:")],
            SELECT_DATE: [CallbackQueryHandler(date_selected, pattern=r"^date:")],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("help", help_command),
            CommandHandler("about", about_command),
        ],
        per_message=False,
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))

    logger.info("Бот запущено...")
    app.run_polling()


if __name__ == "__main__":
    main()
