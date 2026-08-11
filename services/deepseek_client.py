import json

import httpx
import tenacity

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

PROPOSE_MOVIES_TOOL = {
    "type": "function",
    "function": {
        "name": "propose_movies",
        "description": (
            "Предложить пользователю конкретные фильмы, когда уже понятно, что ему подходит."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Оригинальное или общеизвестное название фильма",
                            },
                            "year": {
                                "type": "string",
                                "description": "Год выхода, если известен",
                            },
                            "reason": {
                                "type": "string",
                                "description": "Короткое объяснение, почему фильм подходит запросу",
                            },
                        },
                        "required": ["title"],
                    },
                }
            },
            "required": ["items"],
        },
    },
}


class DeepSeekError(Exception):
    pass


def _should_retry(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TimeoutException):
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
async def _call_api(messages: list[dict]) -> dict:
    async with httpx.AsyncClient(base_url=DEEPSEEK_BASE_URL, timeout=httpx.Timeout(20.0)) as client:
        response = await client.post(
            "/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
            json={
                "model": DEEPSEEK_MODEL,
                "messages": messages,
                "tools": [PROPOSE_MOVIES_TOOL],
                "tool_choice": "auto",
            },
        )
        response.raise_for_status()
        return response.json()


async def get_recommendation_reply(messages: list[dict]) -> dict:
    """Возвращает {"type": "text", "text": ...} или {"type": "movies", "items": [...], "text": ...}."""
    try:
        payload = await _call_api(messages)
    except httpx.TimeoutException as exc:
        raise DeepSeekError("DeepSeek не ответил вовремя, попробуй ещё раз") from exc
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status == 429:
            raise DeepSeekError("DeepSeek сейчас перегружен, попробуй через минуту") from exc
        raise DeepSeekError(f"DeepSeek вернул ошибку {status}") from exc

    try:
        message = payload["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as exc:
        raise DeepSeekError("Неожиданный формат ответа DeepSeek") from exc

    tool_calls = message.get("tool_calls")
    if tool_calls:
        call = tool_calls[0]
        try:
            arguments = json.loads(call["function"]["arguments"])
            items = arguments["items"]
        except (KeyError, ValueError, TypeError) as exc:
            raise DeepSeekError("DeepSeek вернул некорректный вызов инструмента") from exc
        return {"type": "movies", "items": items, "text": message.get("content") or ""}

    return {"type": "text", "text": message.get("content") or ""}
