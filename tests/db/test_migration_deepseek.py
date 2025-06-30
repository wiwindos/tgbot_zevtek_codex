import asyncio

import aiosqlite
import pytest
import pytest_asyncio

from bot import database


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture()
async def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "mig.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    await database.init_db()
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO models(provider, name) VALUES('dipseek','x')",
        )
        await db.commit()
    return db_path


@pytest.mark.asyncio
async def test_migrate_script(temp_db, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", temp_db)
    from scripts.migrate import migrate

    await migrate()
    async with aiosqlite.connect(temp_db) as db:
        cur = await db.execute("SELECT provider FROM models")
        row = await cur.fetchone()
        assert row and row[0] == "deepseek"
