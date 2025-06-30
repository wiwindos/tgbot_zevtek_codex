import asyncio

from bot import database

# mypy: ignore-errors


SQL = "UPDATE models SET provider='deepseek' WHERE provider='dipseek'"


async def migrate() -> None:
    await database.init_db()
    async with database.get_db() as db:
        await db.execute(SQL)
        await db.commit()


if __name__ == "__main__":
    asyncio.run(migrate())
