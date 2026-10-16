import asyncio
import sys
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
import database as db
import handlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)

async def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("\n" + "="*60)
        print("⚠️ УВАГА: Не встановлено BOT_TOKEN у файлі .env!")
        print("1. Отримайте токен у @BotFather в Telegram.")
        print("2. Вкажіть його у файлі d:\\Workspace\\FuelBot_UA\\.env")
        print("   Приклад: BOT_TOKEN=1234567890:ABCdefGhIJKlmNoPqR")
        print("="*60 + "\n")
        return

    # Ініціалізація бази даних
    await db.init_db()
    logger.info("База даних успішно ініціалізована.")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp = Dispatcher()
    dp.include_router(handlers.router)

    logger.info("Запуск Telegram-бота FuelBot_UA...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот зупинений.")
