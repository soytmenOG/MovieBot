from typing import Optional

import httpx
import tenacity

from config import TMDB_API_KEY, TMDB_BASE_URL


class TMDBError(Exception):
    pass


def _should_retry(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code == 429 or exc.response.status_code >= 500
    return False


_retry = tenacity.retry(
    reraise=True,
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=1, max=8),
    retry=tenacity.retry_if_exception(_should_retry),
)


@_retry
async def _fetch_search(title: str, year: Optional[str]) -> dict:
    params = {"query": title, "language": "ru-RU", "api_key": TMDB_API_KEY}
    if year:
        params["year"] = year
    async with httpx.AsyncClient(base_url=TMDB_BASE_URL, timeout=httpx.Timeout(10.0)) as client:
        response = await client.get("/search/movie", params=params)
        response.raise_for_status()
        return response.json()


async def search_movie(title: str, year: Optional[str] = None) -> list[dict]:
    """Ищет фильм в TMDB. Возвращает пустой список, если ничего не нашлось."""
    try:
        payload = await _fetch_search(title, year)
    except httpx.TimeoutException as exc:
        raise TMDBError(f"TMDB не ответил вовремя при поиске «{title}»") from exc
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status == 429:
            raise TMDBError("TMDB сейчас перегружен, попробуй чуть позже") from exc
        raise TMDBError(f"TMDB вернул ошибку {status}") from exc
    except httpx.TransportError as exc:
        raise TMDBError(
            "Не удалось подключиться к TMDB — проверь интернет-соединение (может понадобиться VPN)"
        ) from exc

    try:
        results = payload["results"]
    except (KeyError, TypeError) as exc:
        raise TMDBError("Неожиданный формат ответа TMDB") from exc

    return [
        {
            "tmdb_id": item["id"],
            "title": item.get("title") or item.get("original_title") or title,
            "year": (item.get("release_date") or "")[:4],
            "overview": item.get("overview", ""),
        }
        for item in results[:5]
    ]
