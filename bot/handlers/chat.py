import asyncio

from aiogram import Router
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender

from db import repository
from prompts.system_prompt import build_system_prompt
from services.openrouter_client import OpenRouterError, get_recommendation_reply
from services.tmdb_client import TMDBError, search_movie

router = Router()


@router.message()
async def on_free_text(message: Message) -> None:
    if not message.text:
        return

    user_id = message.from_user.id
    await repository.ensure_user(user_id, message.from_user.username)
    await repository.add_message(user_id, "user", message.text)

    watched = await repository.list_watched_movies(user_id)
    watched_ids = {movie["tmdb_id"] for movie in watched}
    watched_titles = [movie["title"] for movie in watched]

    history = await repository.get_recent_messages(user_id)
    llm_messages = [{"role": "system", "content": build_system_prompt(watched_titles)}]
    llm_messages += [{"role": item["role"], "content": item["content"]} for item in history]

    # Показывает "печатает..." в шапке чата и сам поддерживает статус,
    # пока идёт обращение к LLM и TMDB — без этого долгий ответ выглядит как зависание.
    async with ChatActionSender.typing(bot=message.bot, chat_id=message.chat.id):
        try:
            reply = await get_recommendation_reply(llm_messages)
        except OpenRouterError as exc:
            await message.answer(f"Не получилось получить рекомендацию: {exc}")
            return

        if reply["type"] == "text":
            await repository.add_message(user_id, "assistant", reply["text"])
            await message.answer(reply["text"])
            return

        lookups = await asyncio.gather(
            *(search_movie(item["title"], item.get("year")) for item in reply["items"]),
            return_exceptions=True,
        )

        confirmed = []
        tmdb_error: TMDBError | None = None
        for item, result in zip(reply["items"], lookups):
            if isinstance(result, TMDBError):
                tmdb_error = result
                continue
            candidates = result
            if not candidates:
                continue
            movie = candidates[0]
            if movie["tmdb_id"] in watched_ids:
                continue
            confirmed.append({**movie, "reason": item.get("reason", "")})

        if not confirmed:
            if tmdb_error is not None:
                text = f"Не получилось проверить фильмы через TMDB: {tmdb_error}"
            else:
                text = "Не нашёл подходящих новых вариантов, расскажи чуть подробнее, что тебе интересно."
            await repository.add_message(user_id, "assistant", text)
            await message.answer(text)
            return

        lines = [reply["text"]] if reply["text"] else []
        for movie in confirmed:
            line = f"\n🎬 {movie['title']} ({movie['year']})"
            if movie["reason"]:
                line += f"\n{movie['reason']}"
            elif movie["overview"]:
                line += f"\n{movie['overview'][:200]}"
            lines.append(line)

        text = "\n".join(lines)
        await repository.add_message(user_id, "assistant", text)
        await message.answer(text)
