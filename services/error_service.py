from __future__ import annotations

"""Database helpers for provider error statistics."""

from typing import List, Tuple

from bot import database


async def log_error(provider: str, model: str, error: str) -> None:
    """Insert provider error entry."""
    async with database.get_db() as db:
        await db.execute(
            "INSERT INTO errors(provider, model, error) VALUES(?, ?, ?)",
            (provider, model, error),
        )
        await db.commit()


async def get_recent_summary() -> List[Tuple[str, str, str, int]]:
    """Return aggregated errors for last 24h."""
    async with database.get_db() as db:
        cur = await db.execute(
            """
            SELECT provider, model, error, COUNT(*) n
            FROM errors
            WHERE created_at >= DATETIME('now','-1 day')
            GROUP BY provider, model, error
            ORDER BY n DESC
            """
        )
        rows = await cur.fetchall()
    return [(r[0], r[1], r[2], r[3]) for r in rows]
