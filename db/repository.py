from typing import Any, Optional

import aiosqlite

from config import DB_PATH, HISTORY_LIMIT


async def ensure_user(user_id: int, username: Optional[str]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO users (user_id, username) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET username = excluded.username",
            (user_id, username),
        )
        await db.commit()


async def add_watched_movie(user_id: int, tmdb_id: int, title: str, year: Optional[str]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO watched_movies (user_id, tmdb_id, title, year) VALUES (?, ?, ?, ?)",
            (user_id, tmdb_id, title, year),
        )
        await db.commit()


async def remove_watched_movie(user_id: int, tmdb_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM watched_movies WHERE user_id = ? AND tmdb_id = ?",
            (user_id, tmdb_id),
        )
        await db.commit()


async def list_watched_movies(user_id: int) -> list[dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT tmdb_id, title, year FROM watched_movies WHERE user_id = ? ORDER BY added_at DESC",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def add_message(user_id: int, role: str, content: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content),
        )
        await db.commit()


async def get_recent_messages(user_id: int, limit: int = HISTORY_LIMIT) -> list[dict[str, str]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT role, content FROM messages WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in reversed(rows)]
