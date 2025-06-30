import asyncio

from bot import database

# mypy: ignore-errors


SQL = "UPDATE models SET provider='deepseek' WHERE provider='dipseek'"
CREATE_ERRORS = """
CREATE TABLE IF NOT EXISTS errors(
    id INTEGER PRIMARY KEY,
    provider TEXT,
    model TEXT,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


async def migrate() -> None:
    await database.init_db()
    async with database.get_db() as db:
        await db.execute(SQL)
        await db.execute(CREATE_ERRORS)
        await db.commit()


if __name__ == "__main__":
    asyncio.run(migrate())
