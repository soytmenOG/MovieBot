from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def disambiguation_keyboard(candidates: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for movie in candidates:
        label = f"{movie['title']} ({movie['year']})" if movie["year"] else movie["title"]
        builder.button(text=label, callback_data=f"pick_watched:{movie['tmdb_id']}")
    builder.button(text="Ни один из них", callback_data="pick_watched:none")
    builder.adjust(1)
    return builder.as_markup()


def watched_list_keyboard(movies: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for movie in movies:
        label = f"✕ {movie['title']} ({movie['year']})" if movie["year"] else f"✕ {movie['title']}"
        builder.button(text=label, callback_data=f"remove_watched:{movie['tmdb_id']}")
    builder.adjust(1)
    return builder.as_markup()
