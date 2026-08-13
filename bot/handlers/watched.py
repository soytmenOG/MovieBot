from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.chat_action import ChatActionSender

from bot.keyboards import disambiguation_keyboard, watched_list_keyboard
from db import repository
from services.tmdb_client import TMDBError, search_movie

router = Router()


class WatchedStates(StatesGroup):
    choosing = State()


@router.message(Command("watched"))
async def cmd_watched(message: Message, state: FSMContext) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Использование:\n"
            "/watched <название фильма> — отметить как просмотренный\n"
            "/watched list — посмотреть список просмотренных"
        )
        return

    arg = args[1].strip()
    if arg.lower() == "list":
        movies = await repository.list_watched_movies(message.from_user.id)
        if not movies:
            await message.answer("Список просмотренных пока пуст.")
            return
        await message.answer(
            "Просмотренные фильмы (нажми, чтобы удалить):",
            reply_markup=watched_list_keyboard(movies),
        )
        return

    async with ChatActionSender.typing(bot=message.bot, chat_id=message.chat.id):
        try:
            candidates = await search_movie(arg)
        except TMDBError as exc:
            await message.answer(f"Не получилось найти фильм: {exc}")
            return

    if not candidates:
        await message.answer("Не нашёл такой фильм в базе. Проверь название.")
        return

    if len(candidates) == 1:
        movie = candidates[0]
        await repository.add_watched_movie(
            message.from_user.id, movie["tmdb_id"], movie["title"], movie["year"]
        )
        await message.answer(f"Добавил в просмотренные: {movie['title']} ({movie['year']})")
        return

    await state.set_state(WatchedStates.choosing)
    await state.update_data(candidates=candidates)
    await message.answer(
        "Нашлось несколько фильмов, выбери нужный:",
        reply_markup=disambiguation_keyboard(candidates),
    )


@router.callback_query(WatchedStates.choosing, F.data.startswith("pick_watched:"))
async def on_pick_watched(callback: CallbackQuery, state: FSMContext) -> None:
    choice = callback.data.split(":", 1)[1]
    if choice == "none":
        await state.clear()
        await callback.message.edit_text("Ладно, попробуй уточнить название.")
        await callback.answer()
        return

    data = await state.get_data()
    candidates = data.get("candidates", [])
    movie = next((c for c in candidates if str(c["tmdb_id"]) == choice), None)
    await state.clear()

    if not movie:
        await callback.message.edit_text("Что-то пошло не так, попробуй ещё раз через /watched.")
        await callback.answer()
        return

    await repository.add_watched_movie(
        callback.from_user.id, movie["tmdb_id"], movie["title"], movie["year"]
    )
    await callback.message.edit_text(f"Добавил в просмотренные: {movie['title']} ({movie['year']})")
    await callback.answer()


@router.callback_query(F.data.startswith("remove_watched:"))
async def on_remove_watched(callback: CallbackQuery) -> None:
    tmdb_id = int(callback.data.split(":", 1)[1])
    await repository.remove_watched_movie(callback.from_user.id, tmdb_id)
    movies = await repository.list_watched_movies(callback.from_user.id)
    if movies:
        await callback.message.edit_text(
            "Просмотренные фильмы (нажми, чтобы удалить):",
            reply_markup=watched_list_keyboard(movies),
        )
    else:
        await callback.message.edit_text("Список просмотренных теперь пуст.")
    await callback.answer("Удалено")
