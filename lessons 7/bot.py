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
    MessageHandler,
    filters,
)

from cities import CITIES
from vibe import VIBE_STYLES, run_vibe_agent_async
from weather import get_forecast


class Settings(BaseSettings):
    bot_token: str
    groq_api_key: str

    model_config = {"env_file": ".env"}


settings = Settings()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

SELECT_TYPE, SELECT_CITY, SELECT_DATE, VIBE_STYLE, VIBE_CUSTOM, VIBE_CITY_VIBE = range(6)

UA_WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
UA_MONTHS = [
    "", "січня", "лютого", "березня", "квітня", "травня", "червня",
    "липня", "серпня", "вересня", "жовтня", "листопада", "грудня",
]
UA_WEEKDAYS_FULL = ["понеділок", "вівторок", "середу", "четвер", "п'ятницю", "суботу", "неділю"]


def _mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🌤 Звичайний прогноз", callback_data="mode:regular"),
        InlineKeyboardButton("🌈 Вайб", callback_data="mode:vibe"),
    ]])


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


def _vibe_style_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(label, callback_data=f"vibe_style:{key}")]
        for key, (label, _) in VIBE_STYLES.items()
    ]
    rows.append([InlineKeyboardButton("✍️ Свій стиль", callback_data="vibe_style:custom")])
    return InlineKeyboardMarkup(rows)


def _vibe_city_keyboard() -> InlineKeyboardMarkup:
    cities = sorted(CITIES.keys())
    rows = []
    for i in range(0, len(cities), 3):
        row = [InlineKeyboardButton(c, callback_data=f"vibe_city:{c}") for c in cities[i:i+3]]
        rows.append(row)
    return InlineKeyboardMarkup(rows)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Привіт! Я бот прогнозу погоди для обласних центрів України.\n\n"
        "Оберіть режим:",
        reply_markup=_mode_keyboard(),
    )
    return SELECT_TYPE


async def mode_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    mode = query.data.split(":", 1)[1]

    if mode == "regular":
        await query.edit_message_text("Оберіть місто:", reply_markup=_city_keyboard())
        return SELECT_CITY

    await query.edit_message_text(
        "🌈 ВайбМетеоролог активовано!\n\nОбери стиль прогнозу або напиши свій:",
        reply_markup=_vibe_style_keyboard(),
    )
    return VIBE_STYLE


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


async def vibe_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "🌈 ВайбМетеоролог активовано!\n\nОбери стиль прогнозу або напиши свій:",
        reply_markup=_vibe_style_keyboard(),
    )
    return VIBE_STYLE


async def vibe_style_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    key = query.data.split(":", 1)[1]

    if key == "custom":
        await query.edit_message_text(
            "✍️ Напиши свій стиль прогнозу:\n"
            "(наприклад: «як піrat XVII ст.» або «як Тарас Шевченко»)"
        )
        return VIBE_CUSTOM

    label, description = VIBE_STYLES[key]
    context.user_data["vibe_style"] = description
    context.user_data["vibe_style_label"] = label

    await query.edit_message_text(
        f"Стиль: {label}\n\nОбери місто:",
        reply_markup=_vibe_city_keyboard(),
    )
    return VIBE_CITY_VIBE


async def vibe_custom_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    style_text = update.message.text.strip()
    context.user_data["vibe_style"] = style_text
    context.user_data["vibe_style_label"] = f'«{style_text}»'

    await update.message.reply_text(
        f'Стиль: «{style_text}»\n\nОбери місто:',
        reply_markup=_vibe_city_keyboard(),
    )
    return VIBE_CITY_VIBE


async def vibe_city_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    city = query.data.split(":", 1)[1]
    style = context.user_data.get("vibe_style", "нейтральному")
    style_label = context.user_data.get("vibe_style_label", "")

    await query.edit_message_text(f"⏳ Аналізую вайб для {city}...")

    try:
        result = await run_vibe_agent_async(city, style, settings.groq_api_key)
    except Exception as e:
        logger.error("Vibe agent error: %s: %s", type(e).__name__, e)
        short_error = str(e)[:200]
        await query.edit_message_text(
            f"❌ {type(e).__name__}: {short_error}\n\n/vibe — спробувати знову"
        )
        return ConversationHandler.END

    await query.edit_message_text(
        f"🌈 {city} {style_label}\n\n{result}\n\n/vibe — новий вайб | /start — на початок"
    )
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Доступні команди:\n\n"
        "/start — розпочати (вибір режиму)\n"
        "/vibe — прогноз у творчому стилі (AI)\n"
        "/help — показати цю довідку\n"
        "/about — інформація про бота\n"
        "/cancel — скасувати поточний запит\n\n"
        "Режими:\n"
        "🌤 Звичайний — прогноз на обрану дату\n"
        "🌈 Вайб — AI описує погоду у стилі (Шекспір, Робот, Йог...)\n"
        "або напиши свій стиль!"
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
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("vibe", vibe_start),
        ],
        states={
            SELECT_TYPE:    [CallbackQueryHandler(mode_selected, pattern=r"^mode:")],
            SELECT_CITY:    [CallbackQueryHandler(city_selected, pattern=r"^city:")],
            SELECT_DATE:    [CallbackQueryHandler(date_selected, pattern=r"^date:")],
            VIBE_STYLE:     [CallbackQueryHandler(vibe_style_selected, pattern=r"^vibe_style:")],
            VIBE_CUSTOM:    [MessageHandler(filters.TEXT & ~filters.COMMAND, vibe_custom_text)],
            VIBE_CITY_VIBE: [CallbackQueryHandler(vibe_city_selected, pattern=r"^vibe_city:")],
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
