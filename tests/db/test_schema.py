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
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    await database.init_db()
    return db_path


@pytest.mark.asyncio
async def test_schema_tables(temp_db):
    async with aiosqlite.connect(temp_db) as db:
        await db.execute("PRAGMA foreign_keys=ON")
        query = "SELECT name FROM sqlite_master WHERE type='table';"
        cur = await db.execute(query)
        names = {row[0] for row in await cur.fetchall()}
        assert {"users", "requests", "responses", "models"} <= names

        cur = await db.execute("PRAGMA table_info(requests);")
        cols = {row[1] for row in await cur.fetchall()}
        assert {"user_id", "prompt", "model"} <= cols

        cur = await db.execute("PRAGMA foreign_key_list(responses);")
        fk = await cur.fetchall()
        assert any(row[2] == "requests" for row in fk)


@pytest.mark.asyncio
async def test_foreign_key_constraints(temp_db):
    async with aiosqlite.connect(temp_db) as db:
        await db.execute("PRAGMA foreign_keys=ON")
        # insert user
        user_cur = await db.execute(
            "INSERT INTO users(tg_id, name) VALUES(?, ?)",
            (1, "user"),
        )
        user_id = user_cur.lastrowid
        # insert request
        req_cur = await db.execute(
            "INSERT INTO requests(user_id, prompt, model) VALUES(?, ?, ?)",
            (user_id, "hi", "model"),
        )
        req_id = req_cur.lastrowid
        await db.commit()

        # valid response
        await db.execute(
            "INSERT INTO responses(request_id, content) VALUES(?, ?)",
            (req_id, "ok"),
        )
        await db.commit()

        with pytest.raises(aiosqlite.IntegrityError):
            await db.execute(
                "INSERT INTO responses(request_id, content) VALUES(?, ?)",
                (req_id + 1, "bad"),
            )
            await db.commit()
