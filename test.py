from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(update.message.chat_id)  # Выводим chat ID в консоль
    await update.message.reply_text(f"Chat ID: {update.message.chat_id}")

async def main():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    TOKEN = os.getenv("BOT_TOKEN")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, get_chat_id))
    print("Бот запущен...")
    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())