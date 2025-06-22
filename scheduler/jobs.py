"""Background tasks for refreshing provider models.

The ``models`` table has columns:
```
models(id PK, provider, name, updated_at)
```
``pull_and_sync_models`` compares available provider models with this table and
notifies the admin when new models appear.
"""

from __future__ import annotations

import os
from typing import Sequence

from aiogram import Bot

from bot import database
from bot.utils import send_long_message


async def pull_and_sync_models(
    registry, db_path: str | os.PathLike = database.DB_PATH
) -> None:
    """Fetch models from providers and update the database."""

    async with database.get_db() as db:
        cur = await db.execute("SELECT provider, name FROM models")
        existing = {(row[0], row[1]) for row in await cur.fetchall()}
        initial = not existing

        diff: list[str] = []
        for provider_name, provider in registry._providers.items():
            # registry exposes providers via private field
            models: Sequence[str] = await provider.list_models()
            for model in models:
                key = (provider_name, model)
                if key not in existing:
                    await db.execute(
                        "INSERT INTO models(provider, name, updated_at) "
                        "VALUES(?, ?, CURRENT_TIMESTAMP)",
                        (provider_name, model),
                    )
                    diff.append(model)
                else:
                    await db.execute(
                        "UPDATE models SET updated_at=CURRENT_TIMESTAMP "
                        "WHERE provider=? AND name=?",
                        (provider_name, model),
                    )
        await db.commit()

    if diff and not initial:
        token = os.getenv("BOT_TOKEN", "")
        admin = int(os.getenv("ADMIN_CHAT_ID", "0"))
        if token and admin:
            bot = Bot(token=token)
            text = f"Обновлены модели: {', '.join(diff)}"
            await send_long_message(bot, admin, text)
            await bot.session.close()
