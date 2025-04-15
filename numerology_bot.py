try:
    from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
except ModuleNotFoundError:
    print("\u274c Библиотека 'python-telegram-bot' не установлена. Установите её командой: pip install python-telegram-bot")
    exit()

import os
import re
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from telegram.ext import Application
import uvicorn

logging.basicConfig(level=logging.INFO)

# --- ФУНКЦИЯ ЗАГРУЗКИ ОПИСАНИЙ ---
def load_descriptions(file_path=None):
    if file_path is None:
        file_path = os.path.join(os.path.dirname(__file__), "numerology_data.txt")
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
    except FileNotFoundError:
        logging.error(f"\u274c Файл {file_path} не найден.")
        return {}

    descriptions = {}
    current_num = None
    current_text = []

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue

        match = re.match(r"^(\d{1,2}):(?:\s?.*)?$", line)
        if match:
            if current_num is not None:
                descriptions[current_num] = "\n".join(current_text).strip()
            current_num = int(match.group(1))
            current_text = []
        else:
            current_text.append(line)

    if current_num is not None and current_text:
        descriptions[current_num] = "\n".join(current_text).strip()

    return descriptions

# --- ПЕРЕМЕННЫЕ И НАСТРОЙКИ ---
descriptions = load_descriptions()
ASK_DAY = range(1)[0]
ADMIN_ID = 5786594975

main_menu = ReplyKeyboardMarkup([
    ["\ud83d\udd22 Узнай о себе по дате рождения (бесплатно)"],
    ["\ud83d\udc76 Детская матрица"],
    ["\u2764\ufe0f Отношения", "\ud83e\uddd8\u200d\u2640\ufe0f Здоровье"],
    ["\ud83e\udde0 Личность", "\ud83c\udf1f Миссия души"],
    ["\ud83d\udcbc Реализация и деньги", "\ud83c\udf33 Связь с родом"],
    ["\ud83d\uddd3 Запись на консультацию"],
    ["\ud83d\ude4b\u200d\u2640\ufe0f О себе"]
], resize_keyboard=True)

date_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton(str(i)) for i in range(j, j + 5) if i <= 31] for j in range(1, 32, 5)],
    resize_keyboard=True
)

SECTION_MAP = {
    "\ud83d\udc76 Детская матрица": "В этом разделе я проведу особый нумерологический расчёт и дам тебе знания о твоем ребенке: таланты, энергии и задачи, с которыми он пришёл в этот мир.",
    "\u2764\ufe0f Отношения": "Узнай, какие качества развивать для создания гармоничных отношений.",
    "\ud83e\uddd8\u200d\u2640\ufe0f Здоровье": "Информация о потенциальных заболеваниях и как улучшить физическое состояние.",
    "\ud83e\udde0 Личность": "В этом разделе я дам тебе знания кто ты, какой у тебя характер, какие таланты, твои сильные и слабые стороны, с какой программой ты пришёл в этот мир и какие основные ошибки ты можешь совершить.",
    "\ud83c\udf1f Миссия души": "О глобальной задаче души в этом воплощении.",
    "\ud83d\udcbc Реализация и деньги": "Что влияет на достаток и поток изобилия.",
    "\ud83c\udf33 Связь с родом": "Что даёт связь с родом, родовые задачи и зачем пройти программу."
}

# --- ОБРАБОТЧИКИ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот канала Код души. Цифровая психология и нумерология.\n\n"
        "Выбери, что тебе интересно:",
        reply_markup=main_menu
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user = update.message.from_user
    username = f"@{user.username}" if user.username else user.full_name

    try:
        if text == "\ud83d\udd22 Узнай о себе по дате рождения (бесплатно)":
            await update.message.reply_text("Выбери число рождения (от 1 до 31):", reply_markup=date_keyboard)
            return ASK_DAY

        elif text == "\ud83d\uddd3 Запись на консультацию":
            await update.message.reply_text(
                "Спасибо! Мы свяжемся с вами в ближайшее время.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Записаться", callback_data="consult_Общий запрос")]])
            )

        elif text == "\ud83d\ude4b\u200d\u2640\ufe0f О себе":
            await update.message.reply_text("Я Наталья, специалист по цифровой психологии и нумерологии ✨")

        elif text in SECTION_MAP:
            description = SECTION_MAP[text]
            await update.message.reply_text(
                f'Раздел "{text}". {description}\n\nЧтобы получить подробную консультацию, нажмите кнопку:',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Записаться", callback_data=f"consult_{text}")]])
            )
        else:
            await update.message.reply_text("Пожалуйста, выбери пункт из меню.", reply_markup=main_menu)

    except Exception as e:
        logging.exception("Ошибка в обработчике сообщений:")
        await update.message.reply_text("Произошла техническая ошибка. Попробуйте ещё раз позже.", reply_markup=main_menu)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    section = query.data.replace("consult_", "")
    user = query.from_user
    username = f"@{user.username}" if user.username else user.full_name
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"\ud83d\udce9 Запрос на консультацию\n"
                f"Раздел: {section}\n"
                f"Пользователь: {username} (ID: {user.id})\n"
                f"Время: {now}"
            )
        )
    except Exception as e:
        logging.exception("Ошибка при отправке сообщения администратору")

    await query.edit_message_text("Ваш запрос принят! Мы свяжемся с вами скоро.")

async def process_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit() or not (1 <= int(text) <= 31):
        await update.message.reply_text("Пожалуйста, выбери число от 1 до 31.", reply_markup=date_keyboard)
        return ASK_DAY

    number = int(text)
    max_iterations = 5
    iterations = 0
    while number > 22 and iterations < max_iterations:
        number = sum(int(d) for d in str(number))
        iterations += 1

    result = descriptions.get(number, "Описание не найдено.")
    await update.message.reply_text(f"Ваше число: {number}\n\n{result}", reply_markup=main_menu)
    return ConversationHandler.END

# --- WEBHOOK DEPLOY ---
TOKEN = os.environ.get("TOKEN")
WEBHOOK_HOST = os.environ.get("RENDER_EXTERNAL_URL") or "https://numerology-bot.onrender.com"
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

app = FastAPI()
application = ApplicationBuilder().token(TOKEN).build()

@app.post(WEBHOOK_PATH)
async def telegram_webhook(req: Request):
    update = Update.de_json(await req.json(), application.bot)
    await application.update_queue.put(update)
    return "ok"

@app.on_event("startup")
async def on_startup():
    await application.bot.set_webhook(WEBHOOK_URL)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
        states={ASK_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_day)]},
        fallbacks=[]
    )
    application.add_handler(conv_handler)
    await application.initialize()
    await application.start()
    logging.info("\ud83d\ude80 Бот запущен через Webhook")

@app.on_event("shutdown")
async def on_shutdown():
    await application.stop()
    await application.shutdown()
