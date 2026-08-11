import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.handlers import chat, start, watched
from bot.storage.sqlite_storage import SQLiteStorage
from config import BOT_TOKEN
from db.database import init_db


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    await init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=SQLiteStorage())

    # Порядок важен: команды должны перехватываться раньше,
    # чем catch-all обработчик свободного текста в chat.router.
    dp.include_router(start.router)
    dp.include_router(watched.router)
    dp.include_router(chat.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
