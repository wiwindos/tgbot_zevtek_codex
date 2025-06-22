import asyncio
from datetime import datetime

import pytest
import pytest_asyncio
from aiogram import Bot, types
from aiogram.types import Update

from bot import database
from bot.main import create_bot_and_dispatcher


@pytest.fixture(autouse=True)
def fake_env(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "123:TEST")
    monkeypatch.setenv("ADMIN_CHAT_ID", "999")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture()
async def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "admin.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    await database.init_db()
    return db_path


@pytest.fixture()
def bot_and_dp(monkeypatch, temp_db):
    bot, dp = create_bot_and_dispatcher()

    calls = []

    async def fake_answer(self, text, **kwargs):
        calls.append((self.chat.id, text))
        return types.Message(
            message_id=0,
            date=datetime.now(),
            chat=self.chat,
            from_user=self.from_user,
            text=text,
        )

    async def fake_send(self, chat_id, text, **kwargs):
        calls.append((chat_id, text))
        return types.Message(
            message_id=0,
            date=datetime.now(),
            chat=types.Chat(id=chat_id, type="private"),
            from_user=None,
            text=text,
        )

    monkeypatch.setattr(types.Message, "answer", fake_answer)
    monkeypatch.setattr(Bot, "send_message", fake_send)

    return bot, dp, calls


@pytest.mark.asyncio
async def test_admin_stats(bot_and_dp):
    bot, dp, calls = bot_and_dp
    async with database.get_db() as db:
        for i in range(3):
            await db.execute(
                "INSERT INTO users(tg_id, name, is_active) VALUES(?, ?, ?)",
                (i + 1, f"U{i}", 1 if i < 2 else 0),
            )
        for _ in range(10):
            cur = await db.execute(
                "INSERT INTO requests(user_id, prompt, model) VALUES(?, ?, ?)",
                (1, "p", "m"),
            )
            req_id = cur.lastrowid
            await db.execute(
                "INSERT INTO responses(request_id, content) VALUES(?, ?)",
                (req_id, "r"),
            )
        await db.execute(
            "INSERT INTO files(request_id, path, mime) VALUES(?, ?, ?)",
            (1, "f", "t"),
        )
        await db.commit()

    msg = types.Message(
        message_id=1,
        date=datetime.now(),
        chat=types.Chat(id=999, type="private"),
        from_user=types.User(id=999, is_bot=False, first_name="Admin"),
        text="/admin stats",
    )
    await dp.feed_update(bot, Update(update_id=1, message=msg))

    assert any("Users: 4" in c[1] for c in calls)
    assert any("Requests: 10" in c[1] for c in calls)
    assert any("Files: 1" in c[1] for c in calls)


@pytest.mark.asyncio
async def test_users_pending(bot_and_dp):
    bot, dp, calls = bot_and_dp
    async with database.get_db() as db:
        await db.execute(
            "INSERT INTO users(tg_id, name, is_active) VALUES(?, ?, 0)",
            (123, "Test User"),
        )
        await db.execute(
            "INSERT INTO users(tg_id, name, is_active) VALUES(?, ?, 0)",
            (456, "Alice"),
        )
        await db.commit()

    msg = types.Message(
        message_id=1,
        date=datetime.now(),
        chat=types.Chat(id=999, type="private"),
        from_user=types.User(id=999, is_bot=False, first_name="Admin"),
        text="/admin users pending",
    )
    await dp.feed_update(bot, Update(update_id=2, message=msg))

    assert any("123" in c[1] and "Test User" in c[1] for c in calls)
    assert any("456" in c[1] and "Alice" in c[1] for c in calls)


@pytest.mark.asyncio
async def test_disable_user(bot_and_dp):
    bot, dp, calls = bot_and_dp
    async with database.get_db() as db:
        await db.execute(
            "INSERT INTO users(tg_id, name, is_active) VALUES(?, ?, 1)",
            (123, "User"),
        )
        await db.commit()

    msg = types.Message(
        message_id=1,
        date=datetime.now(),
        chat=types.Chat(id=999, type="private"),
        from_user=types.User(id=999, is_bot=False, first_name="Admin"),
        text="/admin disable 123",
    )
    await dp.feed_update(bot, Update(update_id=3, message=msg))

    async with database.get_db() as db:
        cur = await db.execute("SELECT is_active FROM users WHERE tg_id=123")
        row = await cur.fetchone()
    assert row and row[0] == 0
    assert any(c[0] == 123 and "Доступ временно" in c[1] for c in calls)


@pytest.mark.asyncio
async def test_list_models(bot_and_dp):
    bot, dp, calls = bot_and_dp
    async with database.get_db() as db:
        await db.execute(
            "INSERT INTO models(provider, name, updated_at)"
            " VALUES('g','m1','2024-01-01')"
        )
        await db.execute(
            "INSERT INTO models(provider, name, updated_at)"
            " VALUES('m','m2','2024-01-02')"
        )
        await db.execute(
            "INSERT INTO models(provider, name, updated_at)"
            " VALUES('d','m3','2024-01-03')"
        )
        await db.commit()

    msg = types.Message(
        message_id=1,
        date=datetime.now(),
        chat=types.Chat(id=999, type="private"),
        from_user=types.User(id=999, is_bot=False, first_name="Admin"),
        text="/admin models",
    )
    await dp.feed_update(bot, Update(update_id=4, message=msg))

    assert any("m1" in c[1] for c in calls)
    assert any("m2" in c[1] for c in calls)
    assert any("m3" in c[1] for c in calls)


@pytest.mark.asyncio
async def test_refresh_models(bot_and_dp, monkeypatch):
    bot, dp, calls = bot_and_dp
    called = False

    async def fake_refresh(registry):
        nonlocal called
        called = True
        return ["m-new"]

    monkeypatch.setattr("bot.admin.pull_and_sync_models", fake_refresh)

    msg = types.Message(
        message_id=1,
        date=datetime.now(),
        chat=types.Chat(id=999, type="private"),
        from_user=types.User(id=999, is_bot=False, first_name="Admin"),
        text="/admin refresh models",
    )
    await dp.feed_update(bot, Update(update_id=5, message=msg))

    assert called
    assert any("Модели обновлены" in c[1] for c in calls)
