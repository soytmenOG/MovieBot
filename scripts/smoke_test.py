"""Ручная проверка внешних API без запуска самого бота.

Использование: заполни .env реальными ключами и запусти
    python scripts/smoke_test.py
из корня проекта.
"""

import asyncio
import sys
from pathlib import Path

# Консоль Windows (cp1251) не умеет печатать часть символов из ответов LLM —
# переключаем stdout на UTF-8, чтобы вывод не падал с UnicodeEncodeError.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.openrouter_client import OpenRouterError, get_recommendation_reply  # noqa: E402
from services.tmdb_client import TMDBError, search_movie  # noqa: E402


async def main() -> None:
    print("== TMDB: поиск 'Interstellar' ==")
    try:
        results = await search_movie("Interstellar")
        for movie in results:
            print(f"- {movie['title']} ({movie['year']})")
    except TMDBError as exc:
        print(f"Ошибка TMDB: {exc}")

    print("\n== OpenRouter: тестовый запрос ==")
    try:
        reply = await get_recommendation_reply(
            [
                {"role": "system", "content": "Ты помощник по подбору фильмов. Отвечай кратко."},
                {"role": "user", "content": "Посоветуй фантастику про космос"},
            ]
        )
        print(reply)
    except OpenRouterError as exc:
        print(f"Ошибка OpenRouter: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
