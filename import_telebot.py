from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters, ConversationHandler
from telegram.constants import ParseMode
import datetime
import os
import json
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VACANCY_FILE = os.path.join(BASE_DIR, "vacancies.json")

# 🔧 Глобальная настройка
WITH_IMAGES = False

# Telegram ID для заявок
ADMIN_ID = -1002865584189

# 🔧 ID тем
THREAD_IDS = {
    "#solo": 47,
    "#cp": 45,
    "#recruit": 51,
    "#vacancy": 66,       # тема для вакансий
    "#join_vacancy": 73   # тема для заявок на вступление в КП
}

# Разрешённые пользователи для создания вакансий
ALLOWED_IDS = [394324214, 657316611, 293183798, 5310199168, 580709477, 1317317174, 269650718, 1749349659, 1264264185, 140066716, 626603698, 519580140, 1452497431, 339954863, 368411580, 399010961, 5004309519, 1599041162, 1111303399, 1186568080]

# Вопросы
SOLO_QUESTIONS = [
    {"question": "Ваше имя?", "image": "1.jpg"},
    {"question": "Возраст?", "image": "1.jpg"},
    {"question": "Игровой ник?", "image": "1.jpg"},
    {"question": "Кем планируешь играть?", "image": "1.jpg"},
    {"question": "Время игры (прайм)?", "image": "1.jpg"},
    {"question": "Как с тобой связаться? (контакт в тг)", "image": "1.jpg"}
]

RECRUIT_QUESTIONS = [
    {"question": "Планируемый тип группы? (мили, луки, маги...)", "image": "1.jpg"},
    {"question": "Нужно ли добирать игроков до полной группы?", "image": "1.jpg"},
    {"question": "Прайм группы? (время по Мск)", "image": "1.jpg"},
    {"question": "Контакты ПЛа?", "image": "1.jpg"}
]

CP_QUESTIONS = [
    {"question": "Ваше имя?", "image": "1.jpg"},
    {"question": "Возраст?", "image": "1.jpg"},
    {"question": "Игровой ник?", "image": "1.jpg"},
    {"question": "Кем планируешь играть?", "image": "1.jpg"},
    {"question": "Время игры (прайм)?", "image": "1.jpg"},
    {"question": "Как с тобой связаться? (контакт в тг)", "image": "1.jpg"}
]

VACANCY_QUESTIONS = [
    {"question": "Название КП", "image": "1.jpg"},
    {"question": "Прайм по Мск", "image": "1.jpg"},
    {"question": "Какие профессии ищете?", "image": "1.jpg"},
    {"question": "Доп. требования", "image": "1.jpg"},
    {"question": "Информация о КП в свободной форме", "image": "1.jpg"},
    {"question": "Контакты ПЛа", "image": "1.jpg"}
]

JOIN_VACANCY_QUESTIONS = [
    {"question": "Ваше имя?", "image": "1.jpg"},
    {"question": "Возраст?", "image": "1.jpg"},
    {"question": "Игровой ник?", "image": "1.jpg"},
    {"question": "Класс/роль, которой хотите играть?", "image": "1.jpg"},
    {"question": "Время игры (прайм)?", "image": "1.jpg"},
    {"question": "Контакты (контакт в ТГ)?", "image": "1.jpg"}
]

# Этапы
SELECT_TYPE, ASKING, CONFIRM = range(3)

# Временное хранилище
last_submission_time = {}

# ===== Работа с файлами =====
def load_vacancies():
    if not os.path.exists(VACANCY_FILE):
        return []
    with open(VACANCY_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_vacancy(vacancy):
    vacancies = load_vacancies()
    vacancies.append(vacancy)
    with open(VACANCY_FILE, "w", encoding="utf-8") as f:
        json.dump(vacancies, f, ensure_ascii=False, indent=2)

# ===== Команды =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [
        [InlineKeyboardButton("Я соло игрок", callback_data='#solo')],
        [InlineKeyboardButton("Я ищу КП", callback_data='#cp')],
        [InlineKeyboardButton("МЫ (КП) ищем клан", callback_data='#recruit')],
        [InlineKeyboardButton("Создать вакансию (кнопка для членов клана)", callback_data='#vacancy')],
        [InlineKeyboardButton("Показать все вакансии", callback_data='#show_vacancies')]
    ]

    if update.message:
        await update.message.reply_text("Выберите тип заявки:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.reply_text("Выберите тип заявки:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_TYPE

# ===== Обработка кнопок =====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    form_type = query.data

    # Показ вакансий
    if form_type == '#show_vacancies':
        vacancies = load_vacancies()
        if not vacancies:
            await query.edit_message_text("Пока нет доступных вакансий.")
            return ConversationHandler.END

        await query.edit_message_text("📋 Доступные вакансии:")

        text_lines = ["📋 Доступные вакансии:"]
        keyboard = []
        for v in vacancies:
            name = v.get("name")
            prime = v.get("prime")
            looking = v.get("looking")
            requirements = v.get("requirements")
            info = v.get("info")
            
            if not name:
                continue

            vacancy_text = (
                "━━━━━━━━━━━━\n"
                f"➡️ <b>{name}</b>\n"
                f"🕒 Прайм: {prime}\n"
                f"🎯 Ищем: {looking}\n"
                f"📌 Требования: {requirements}\n"
                f"ℹ️ О КП: {info}\n"
                "━━━━━━━━━━━━"
            )

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"Хочу в {name}", callback_data=f"joinvac_{name}")]
            ])

            await query.message.reply_text(
                vacancy_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )

        return SELECT_TYPE

    # Доступ к созданию вакансии
    if form_type == '#vacancy' and user_id not in ALLOWED_IDS:
        await query.edit_message_text("Извините, вы не являетесь членом клана Svetlana Petrovna")
        return ConversationHandler.END

    # Заявка на вакансию
    if form_type.startswith("joinvac_"):
        context.user_data['form_type'] = '#join_vacancy'
        context.user_data['vacancy_name'] = form_type.replace("joinvac_", "")
        context.user_data['answers'] = []
        context.user_data['current_q'] = 0
        context.user_data['questions'] = JOIN_VACANCY_QUESTIONS

        q = JOIN_VACANCY_QUESTIONS[0]['question']
        await query.message.reply_text(
            f"Вы подаёте заявку на вступление в КП <b>{context.user_data['vacancy_name']}</b>\n\n{q}",
            parse_mode=ParseMode.HTML
        )
        return ASKING

    # Ограничение по времени (не для вакансий)
    if form_type != '#vacancy':
        last_time = last_submission_time.get(user_id)
        if last_time and (datetime.datetime.now() - last_time).seconds < 3600:
            await query.edit_message_text("Вы уже отправляли заявку. Подождите час перед следующей.")
            return ConversationHandler.END

    # Сброс анкеты
    context.user_data['form_type'] = form_type
    context.user_data['answers'] = []
    context.user_data['current_q'] = 0

    if form_type == '#recruit':
        questions = RECRUIT_QUESTIONS
    elif form_type == '#cp':
        questions = CP_QUESTIONS
    elif form_type == '#vacancy':
        questions = VACANCY_QUESTIONS
    else:
        questions = SOLO_QUESTIONS

    context.user_data['questions'] = questions
    await query.message.reply_text(questions[0]['question'])
    return ASKING

# ===== Сбор ответов =====
async def collect_answers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data['answers'].append(text)
    context.user_data['current_q'] += 1

    questions = context.user_data['questions']
    if context.user_data['current_q'] < len(questions):
        await update.message.reply_text(questions[context.user_data['current_q']]['question'])
        return ASKING
    else:
        form_type = context.user_data['form_type']
        answers = context.user_data['answers']
        preview_text = f"📝 Ваша анкета ({form_type}):\n\n"
        for q, a in zip(questions, answers):
            preview_text += f"<b>{q['question']}</b> {a}\n"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Отправить", callback_data="confirm_submit")],
            [InlineKeyboardButton("✏️ Редактировать", callback_data="edit_form")],
            [InlineKeyboardButton("🔄 Сменить тип анкеты", callback_data="#change")]
        ])
        await update.message.reply_text(preview_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return CONFIRM

# ===== Подтверждение =====
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
            text += f"<b>{q['question']}</b> {a}\n"

        # если вакансия — сохраняем
        if form_type == '#vacancy':
            vacancy = {
                "name": answers[0],
                "prime": answers[1],
                "looking": answers[2],
                "requirements": answers[3],
                "info": answers[4],
                "recruiter": answers[5]
            }
            save_vacancy(vacancy)

        # если заявка на вакансию — добавляем рекрутера
        if form_type == '#join_vacancy':
            vacancy_name = context.user_data.get("vacancy_name")
            recruiter = None
            vacancies = load_vacancies()
            for v in vacancies:
                if v.get("name") == vacancy_name:
                    recruiter = v.get("recruiter")
                    break
            text += f"\n\n👤 Рекрутер КП <b>{vacancy_name}</b>: {recruiter or 'не указан'}"

        # отправка
        thread_id = THREAD_IDS.get(form_type)
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=text,
            parse_mode=ParseMode.HTML,
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

# ===== Служебные команды =====
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Заявка отменена.")
    return ConversationHandler.END

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    await update.message.reply_text(f"Chat ID этой переписки: <code>{chat_id}</code>", parse_mode=ParseMode.HTML)

# ===== Запуск =====
def main():
    load_dotenv()
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("BOT_TOKEN не найден в .env файле")

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
                CommandHandler('start', start),
                CallbackQueryHandler(button_handler)
            ],
            CONFIRM: [
                CallbackQueryHandler(confirm_handler, pattern="^confirm_submit$"),
                CallbackQueryHandler(confirm_handler, pattern="^edit_form$"),
                CallbackQueryHandler(button_handler)
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
