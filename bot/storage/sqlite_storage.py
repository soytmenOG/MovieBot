import json
from typing import Any, Dict, Optional

import aiosqlite
from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StorageKey

from config import DB_PATH


class SQLiteStorage(BaseStorage):
    """aiogram FSM storage backed by the fsm_state table instead of an in-memory dict."""

    async def set_state(self, key: StorageKey, state: Any = None) -> None:
        state_str = state.state if isinstance(state, State) else state
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO fsm_state (user_id, chat_id, state, data) VALUES (?, ?, ?, '{}') "
                "ON CONFLICT(user_id, chat_id) DO UPDATE SET state = excluded.state",
                (key.user_id, key.chat_id, state_str),
            )
            await db.commit()

    async def get_state(self, key: StorageKey) -> Optional[str]:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT state FROM fsm_state WHERE user_id = ? AND chat_id = ?",
                (key.user_id, key.chat_id),
            )
            row = await cursor.fetchone()
            return row[0] if row else None

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO fsm_state (user_id, chat_id, state, data) VALUES (?, ?, NULL, ?) "
                "ON CONFLICT(user_id, chat_id) DO UPDATE SET data = excluded.data",
                (key.user_id, key.chat_id, json.dumps(data)),
            )
            await db.commit()

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT data FROM fsm_state WHERE user_id = ? AND chat_id = ?",
                (key.user_id, key.chat_id),
            )
            row = await cursor.fetchone()
            return json.loads(row[0]) if row and row[0] else {}

    async def close(self) -> None:
        pass
