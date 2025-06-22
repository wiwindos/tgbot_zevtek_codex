"""User management service.

Handles creation and activation of Telegram users.
`is_active` indicates whether the user is allowed to interact with the bot.
"""

from typing import Any, Dict, List

from bot import database


async def get_or_create_user(tg_id: int, name: str) -> Dict[str, Any]:
    """Return user record, creating it if necessary."""
    async with database.get_db() as db:
        cur = await db.execute(
            "SELECT id, is_active FROM users WHERE tg_id = ?",
            (tg_id,),
        )
        row = await cur.fetchone()
        if row:
            return {"id": row[0], "is_active": row[1]}

        cur = await db.execute(
            "INSERT INTO users(tg_id, name, requested_at)\n"
            "VALUES(?, ?, CURRENT_TIMESTAMP)",
            (tg_id, name),
        )
        await db.commit()
        return {"id": cur.lastrowid, "is_active": 0}


async def set_active(tg_id: int, value: bool) -> None:
    """Update user active status."""
    async with database.get_db() as db:
        await db.execute(
            "UPDATE users SET is_active = ? WHERE tg_id = ?",
            (1 if value else 0, tg_id),
        )
        await db.commit()


async def pending_users() -> List[Dict[str, Any]]:
    """Return list of users waiting for approval."""
    async with database.get_db() as db:
        cur = await db.execute(
            "SELECT tg_id, name FROM users WHERE is_active = 0",
        )
        rows = await cur.fetchall()
        return [{"tg_id": r[0], "name": r[1]} for r in rows]
