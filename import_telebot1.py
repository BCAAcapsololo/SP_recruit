from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters, ConversationHandler
from telegram.constants import ParseMode
import datetime
import os
from dotenv import load_dotenv

BASE_DIR = r"C:\Users\BCAAcaps\Desktop\SP bot\images"

# 🔧 Глобальная настройка: показывать картинки или нет
WITH_IMAGES = False   # Если False → будут только текстовые вопросы

# Telegram ID для отправки заявок (группа)
ADMIN_ID = -1002865584189  # замените на ваш ID

# 🔧 Укажи ID тем для разных типов заявок
THREAD_IDS = {
    "#solo": 47,     # ID темы для соло игроков
    "#cp": 45,       # ID темы для поиска КП
    "#recruit": 51   # ID темы для КП, которые ищут игроков
}

# Вопросы и картинки для разных ролей
SOLO_QUESTIONS = [
    {"question": "Ваше имя?", "image": "1.jpg"},
    {"question": "Возраст?", "image": "1.jpg"},
    {"question": "Игровой ник?", "image": "1.jpg"},
    {"question": "Кем планируешь играть?", "image": "1.jpg"},
    # {"question": "Уровень мейна (если уже начал играть)? ", "image": "1.jpg"},
    # {"question": "Какие сабы и их уровни?", "image": "1.jpg"},
    # {"question": "Готовы ли вы к реролу или игре на клановом персонаже?", "image": "1.jpg"},
    {"question": "Время игры (прайм)?", "image": "1.jpg"}
]

RECRUIT_QUESTIONS = [
    {"question": "Планируемый тип группы? К примеру: мили, луки, маги, стоп-пак", "image": "1.jpg"},
    {"question": "Нужно ли вам добирать игроков до полной группы?", "image": "1.jpg"},
    {"question": "Прайм группы? Время по Мск", "image": "1.jpg"},
    {"question": "Контакты ПЛа?", "image": "1.jpg"}
]

CP_QUESTIONS = [
    {"question": "Ваше имя?", "image": "1.jpg"},
    {"question": "Возраст?", "image": "1.jpg"},
    {"question": "Игровой ник?", "image": "1.jpg"},
    {"question": "Кем планируешь играть?", "image": "1.jpg"},
    # {"question": "Уровень мейна (если уже начал играть)? ", "image": "1.jpg"},
    # {"question": "Какие сабы и их уровни?", "image": "1.jpg"},
    # {"question": "Готовы ли вы к реролу или игре на клановом персонаже?", "image": "1.jpg"},
    {"question": "Время игры (прайм)?", "image": "1.jpg"}
]

# Этапы диалога
SELECT_TYPE, ASKING, CONFIRM = range(3)

# Временное хранилище
last_submission_time = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    keyboard = [
        [InlineKeyboardButton("Я соло игрок", callback_data='#solo')],
        [InlineKeyboardButton("Я ищу КП", callback_data='#cp')],
        [InlineKeyboardButton("МЫ (КП) ищем клан", callback_data='#recruit')]
    ]

    if update.message:
        await update.message.reply_text("Выберите тип заявки:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.reply_text("Выберите тип заявки:", reply_markup=InlineKeyboardMarkup(keyboard))

    return SELECT_TYPE

# Обработка выбора типа анкеты
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    last_time = last_submission_time.get(user_id)
    if last_time and (datetime.datetime.now() - last_time).seconds < 3600:
        await query.edit_message_text("Вы уже отправляли заявку. Подождите час перед следующей.")
        return ConversationHandler.END

    form_type = query.data
    context.user_data['form_type'] = form_type
    context.user_data['answers'] = []
    context.user_data['current_q'] = 0

    if form_type == '#recruit':
        questions = RECRUIT_QUESTIONS
    elif form_type == '#cp':
        questions = CP_QUESTIONS
    else:
        questions = SOLO_QUESTIONS

    context.user_data['questions'] = questions
    question = questions[0]['question']
    image_path = os.path.join(BASE_DIR, questions[0]['image'])

    if WITH_IMAGES:
        if os.path.exists(image_path):
            with open(image_path, 'rb') as img:
                await query.message.reply_photo(photo=img, caption=question)
        else:
            await query.message.reply_text(question)
    else:
        await query.message.reply_text(question)

    return ASKING

# Сбор ответов
async def collect_answers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data['answers'].append(text)
    context.user_data['current_q'] += 1

    questions = context.user_data['questions']
    if context.user_data['current_q'] < len(questions):
        next_q = questions[context.user_data['current_q']]['question']
        image_path = os.path.join(BASE_DIR, questions[context.user_data['current_q']]['image'])

        if WITH_IMAGES:
            with open(image_path, 'rb') as img:
                await update.message.reply_photo(photo=img, caption=next_q)
        else:
            await update.message.reply_text(next_q)
        return ASKING
    else:
        form_type = context.user_data['form_type']
        answers = context.user_data['answers']
        questions = context.user_data['questions']

        preview_text = f"📝 Ваша анкета ({form_type}):\n\n"
        for q, a in zip(questions, answers):
            preview_text += f"*{q['question']}* {a}\n"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Отправить", callback_data="confirm_submit")],
            [InlineKeyboardButton("✏️ Редактировать", callback_data="edit_form")]
        ])

        await update.message.reply_text(preview_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        return CONFIRM

# Подтверждение отправки или редактирование
async def confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    form_type = context.user_data['form_type']
    answers = context.user_data['answers']
    questions = context.user_data['questions']

    if query.data == "confirm_submit":
        text = f"📨 Новая заявка ({form_type}):\n\n"
        for q, a in zip(questions, answers):
            text += f"*{q['question']}* {a}\n"

        # ✅ выбираем тему для отправки
        thread_id = THREAD_IDS.get(form_type)

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            message_thread_id=thread_id
        )

        await query.edit_message_text("✅ Заявка отправлена. Спасибо!")
        last_submission_time[user_id] = datetime.datetime.now()
        return ConversationHandler.END

    elif query.data == "edit_form":
        context.user_data['answers'] = []
        context.user_data['current_q'] = 0
        await query.edit_message_text(f"Хорошо, начнём заново.\n\n{questions[0]['question']}")
        return ASKING

# Команда /cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Заявка отменена.")
    return ConversationHandler.END

# Команда /getchatid
async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    await update.message.reply_text(f"Chat ID этой переписки: `{chat_id}`", parse_mode=ParseMode.MARKDOWN)

# Основная функция
def main():
    load_dotenv()
    TOKEN = os.getenv("BOT_TOKEN")
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_TYPE: [
                CallbackQueryHandler(button_handler),
                CommandHandler('start', start)
            ],
            ASKING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_answers),
                CommandHandler('start', start)
            ],
            CONFIRM: [
                CallbackQueryHandler(confirm_handler, pattern="^confirm_submit$"),
                CallbackQueryHandler(confirm_handler, pattern="^edit_form$")
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CommandHandler('start', start)
        ],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("getchatid", get_chat_id))

    print("Бот запущен...")
    app.run_polling()

if __name__ == '__main__':
    main()
