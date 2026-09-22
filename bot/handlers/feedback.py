import httpx
from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from config import FEEDBACK_WEBHOOK_URL

router = Router()

# Слова-триггеры для тихого автоопределения жалоб в обычных сообщениях
# (не все пишут явно через /feedback).
ISSUE_KEYWORDS = (
    "сломал",
    "не работает",
    "не работал",
    "поломк",
    "глюк",
    "баг",
    "завис",
    "не отвечает",
    "ошибк",
    "не отправляет",
    "не открывает",
)


def contains_issue_keywords(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in ISSUE_KEYWORDS)


async def send_to_pipeline(text: str) -> bool:
    """Пересылает текст в n8n-вебхук. Возвращает True при успехе."""
    if not FEEDBACK_WEBHOOK_URL:
        return False
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            response = await client.post(FEEDBACK_WEBHOOK_URL, json={"text": text})
            response.raise_for_status()
    except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.TransportError):
        return False
    return True


@router.message(Command("feedback"))
async def cmd_feedback(message: Message, command: CommandObject) -> None:
    text = (command.args or "").strip()
    if not text:
        await message.answer(
            "Использование: /feedback <текст>\n"
            "Например: /feedback бот завис после нажатия кнопки"
        )
        return

    ok = await send_to_pipeline(text)
    if ok:
        await message.answer("Спасибо за отзыв! Я его записал и разберу в ближайшее время.")
    else:
        await message.answer("Спасибо за отзыв! Автоматическая обработка сейчас недоступна, но я его увидел.")
