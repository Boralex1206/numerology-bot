try:
    from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
except ModuleNotFoundError:
    print("❌ Библиотека 'python-telegram-bot' не установлена. Установите её командой: pip install python-telegram-bot")
    exit()

import os
import re
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

# Загрузка расшифровок из TXT-файла

def load_descriptions(file_path=None):
    if file_path is None:
        file_path = os.path.join(os.path.dirname(__file__), "numerology_data.txt")
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
    except FileNotFoundError:
        logging.error(f"❌ Файл {file_path} не найден.")
        return {}

    descriptions = {}
    current_num = None
    current_text = []

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.match(r"^\d{1,2}:$", line):
            if current_num is not None:
                descriptions[current_num] = "\n".join(current_text).strip()
            current_num = int(line[:-1])
            current_text = []
        else:
            current_text.append(line)

    if current_num is not None and current_text:
        descriptions[current_num] = "\n".join(current_text).strip()

    return descriptions

descriptions = load_descriptions()

ASK_DAY = range(1)[0]

ADMIN_ID = 5786594975

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
    "👶 Детская матрица": "В этом разделе я проведу особый нумерологический расчёт и дам тебе знания о твоем ребенке: таланты, энергии и задачи, с которыми он пришёл в этот мир.",
    "❤️ Отношения": "Узнай, какие качества развивать для создания гармоничных отношений.",
    "🧘‍♀️ Здоровье": "Информация о потенциальных заболеваниях и как улучшить физическое состояние.",
    "🧠 Личность": "В этом разделе я дам тебе знания кто ты, какой у тебя характер, какие таланты, твои сильные и слабые стороны, с какой программой ты пришёл в этот мир и какие основные ошибки ты можешь совершить.",
    "🌟 Миссия души": "О глобальной задаче души в этом воплощении.",
    "💼 Реализация и деньги": "Что влияет на достаток и поток изобилия.",
    "🌳 Связь с родом": "Что даёт связь с родом, родовые задачи и зачем пройти программу."
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот канала Код души. Цифровая психология и нумерология.\n\n"
        "Нумерология — это наука, изучающая взаимосвязь чисел и любых явлений, происходящих в мире. "
        "Самым главным числовым кодом, оказывающим огромное влияние на жизнь человека, является дата рождения. "
        "Она несёт в себе уникальную информацию, и если расшифровать её с помощью нумерологических знаний, то можно увидеть разные "
        "аспекты жизни человека, его характер, таланты, кармические задачи, миссию данного воплощения, его прошлое и будущее.\n\n"
        "Выбери, что тебе интересно:",
        reply_markup=main_menu
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user = update.message.from_user
    username = f"@{user.username}" if user.username else user.full_name

    try:
        if text == "🔢 Узнай о себе по дате рождения (бесплатно)":
            await update.message.reply_text("Выбери число рождения (от 1 до 31):", reply_markup=date_keyboard)
            return ASK_DAY

        elif text == "🗓 Запись на консультацию":
            await update.message.reply_text(
                "Спасибо! Мы свяжемся с вами в ближайшее время.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Записаться", callback_data="consult_Общий запрос")]])
            )

        elif text == "🙋‍♀️ О себе":
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
                f"📩 Запрос на консультацию\n"
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

if __name__ == '__main__':
    app = ApplicationBuilder().token(os.environ.get("TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
        states={ASK_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_day)]},
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("Бот запущен...")
    app.run_polling()
