import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode

from bot.handlers import chat, feedback, start, watched
from bot.storage.sqlite_storage import SQLiteStorage
from config import BOT_TOKEN, PROXY_URL
from db.database import init_db


async def main() -> None:
    # Консоль Windows (cp1251) не умеет печатать часть символов из логов aiogram/LLM.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO)
    await init_db()

    session = AiohttpSession(proxy=PROXY_URL) if PROXY_URL else None
    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=SQLiteStorage())

    # Порядок важен: команды должны перехватываться раньше,
    # чем catch-all обработчик свободного текста в chat.router.
    dp.include_router(start.router)
    dp.include_router(watched.router)
    dp.include_router(feedback.router)
    dp.include_router(chat.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
