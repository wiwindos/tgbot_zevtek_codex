import pathlib

import aiosqlite

DB_PATH = pathlib.Path("bot.db")

CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users(
    id     INTEGER PRIMARY KEY,
    tg_id  INTEGER UNIQUE,
    name   TEXT
);
"""


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_USERS)
        await db.commit()
