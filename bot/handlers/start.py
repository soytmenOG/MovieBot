from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from db import repository

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await repository.ensure_user(message.from_user.id, message.from_user.username)
    await message.answer(
        "Привет! Я помогу подобрать фильм под настроение.\n\n"
        "Просто расскажи, что хочешь посмотреть — например: "
        "«хочу что-то грустное, но со светлым финалом» или "
        "«посоветуй что-то в духе Интерстеллара».\n\n"
        "Команда /watched — отметить фильмы, которые ты уже смотрел, "
        "чтобы я их больше не советовал."
    )
