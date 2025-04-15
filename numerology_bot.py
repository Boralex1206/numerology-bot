import os
import re
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, filters,
                          ContextTypes, ConversationHandler, CallbackQueryHandler, Application)
import uvicorn

logging.basicConfig(level=logging.INFO)

# --- Константы ---
ASK_DAY = range(1)[0]
ADMIN_ID = 5786594975  # Замени на свой Telegram ID
TOKEN = os.environ.get("TOKEN")
WEBHOOK_HOST = os.environ.get("RENDER_EXTERNAL_URL") or "https://numerology-bot.onrender.com"
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# --- Интерфейсы ---
main_menu = ReplyKeyboardMarkup([
    ["🔢 Узнай о себе по дате рождения (бесплатно)"],
    ["👶 Детская матрица"],
    ["❤️ Отношения", "🧘‍♀️ Здоровье"],
    ["🧠 Личность", "🌟 Миссия души"],
    ["💼 Реализация и деньги", "🌳 Связь с родом"],
    ["🗓 Запись на консультацию"],
    ["🙋‍♀️ О себе"]
], resize_keyboard=True)

date_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton(str(i)) for i in range(j, j + 5) if i <= 31] for j in range(1, 32, 5)],
    resize_keyboard=True
)

SECTION_MAP = {
    "👶 Детская матрица": "В этом разделе я проведу особый нумерологический расчёт и дам тебе знания о твоем ребёнке: таланты, энергии и задачи, с которыми он пришёл в этот мир.",
    "❤️ Отношения": "Узнай, какие качества развивать для создания гармоничных отношений.",
    "🧘‍♀️ Здоровье": "Информация о потенциальных заболеваниях и как улучшить физическое состояние.",
    "🧠 Личность": "Кто ты, твой характер, таланты, сильные и слабые стороны, программы и ошибки.",
    "🌟 Миссия души": "О глобальной задаче души в этом воплощении.",
    "💼 Реализация и деньги": "Что влияет на достаток и поток изобилия.",
    "🌳 Связь с родом": "Что даёт связь с родом, родовые задачи и зачем пройти программу."
}

# --- Загрузка описаний из файла ---
def load_descriptions():
    path = os.path.join(os.path.dirname(__file__), "numerology_data.txt")
    descriptions = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        logging.error("Файл numerology_data.txt не найден.")
        return descriptions

    current_number = None
    buffer = []
    for line in content.splitlines():
        line = line.strip()
        if re.fullmatch(r"\d{1,2}:", line):
            if current_number and buffer:
                descriptions[current_number] = "\n".join(buffer).strip()
            current_number = int(line[:-1])
            buffer = []
        else:
            buffer.append(line)
    if current_number and buffer:
        descriptions[current_number] = "\n".join(buffer).strip()

    return descriptions

descriptions = load_descriptions()

# --- Хэндлеры ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот канала Код души. Цифровая психология и нумерология.\n\nВыбери, что тебе интересно:",
        reply_markup=main_menu
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "🔢 Узнай о себе по дате рождения (бесплатно)":
        await update.message.reply_text("Выбери число рождения (от 1 до 31):", reply_markup=date_keyboard)
        return ASK_DAY
    elif text in SECTION_MAP:
        await update.message.reply_text(
            f'{SECTION_MAP[text]}\n\nЧтобы получить подробную консультацию, нажми кнопку:',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Записаться", callback_data=f"consult_{text}")]])
        )
    elif text == "🗓 Запись на консультацию":
        await update.message.reply_text("Выберите раздел, по которому хотите консультацию:", reply_markup=main_menu)
    elif text == "🙋‍♀️ О себе":
        await update.message.reply_text("Я Наталья, специалист по цифровой психологии и нумерологии ✨")
    else:
        await update.message.reply_text("Пожалуйста, выбери пункт из меню.", reply_markup=main_menu)

async def process_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("Пожалуйста, введите число от 1 до 31:", reply_markup=date_keyboard)
        return ASK_DAY

    day = int(text)
    while day > 22:
        day = sum(map(int, str(day)))

    message = descriptions.get(day, "Описание не найдено.")
    await update.message.reply_text(f"Ваше число: {day}\n\n{message}", reply_markup=main_menu)
    return ConversationHandler.END

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    section = query.data.replace("consult_", "")
    user = query.from_user
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 Запрос на консультацию\nРаздел: {section}\nПользователь: @{user.username or user.full_name}\nID: {user.id}\nВремя: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    await query.edit_message_text("Ваш запрос принят! Мы свяжемся с вами скоро.")

# --- Приложение FastAPI и Webhook ---
app = FastAPI()
application = ApplicationBuilder().token(TOKEN).build()

@app.post(WEBHOOK_PATH)
async def webhook_handler(request: Request):
    update = Update.de_json(await request.json(), application.bot)
    await application.update_queue.put(update)
    return "ok"

@app.on_event("startup")
async def startup():
    await application.bot.set_webhook(WEBHOOK_URL)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔢.*"), handle_message)],
        states={ASK_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_day)]},
        fallbacks=[]
    )
    application.add_handler(conv)
    # 👇 Этот хендлер обрабатывает все остальные текстовые сообщения
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await application.initialize()
    await application.start()
    logging.info("🚀 Бот запущен через Webhook")

@app.on_event("shutdown")
async def shutdown():
    await application.stop()
    await application.shutdown()

# --- Запуск (только локально) ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=1000, reload=True)
