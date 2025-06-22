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
    db_path = tmp_path / "auth.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    await database.init_db()
    return db_path


@pytest_asyncio.fixture()
async def bot_and_dp(monkeypatch, temp_db):
    bot, dp = create_bot_and_dispatcher()

    calls = []

    async def fake_answer(self, text, **kwargs):
        calls.append((self.chat.id, text, kwargs))
        return types.Message(
            message_id=0,
            date=datetime.now(),
            chat=self.chat,
            from_user=self.from_user,
            text=text,
        )

    async def fake_send(self, chat_id, text, **kwargs):
        calls.append((chat_id, text, kwargs))
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
async def test_authorization_flow(bot_and_dp):
    bot, dp, calls = bot_and_dp

    start_msg = types.Message(
        message_id=1,
        date=datetime.now(),
        chat=types.Chat(id=123, type="private"),
        from_user=types.User(id=123, is_bot=False, first_name="User"),
        text="/start",
    )
    await dp.feed_update(bot, Update(update_id=1, message=start_msg))

    assert len(calls) == 2
    user_chat, user_text, _ = calls[0]
    assert user_chat == 123
    assert "заявка" in user_text.lower()

    admin_chat, _, kwargs = calls[1]
    assert admin_chat == 999
    keyboard = kwargs.get("reply_markup")
    assert keyboard is not None
    assert "Одобрить" in keyboard.inline_keyboard[0][0].text

    async with database.get_db() as db:
        cur = await db.execute("SELECT is_active FROM users WHERE tg_id=123")
        row = await cur.fetchone()
        assert row and row[0] == 0

    approve_msg = types.Message(
        message_id=2,
        date=datetime.now(),
        chat=types.Chat(id=999, type="private"),
        from_user=types.User(id=999, is_bot=False, first_name="Admin"),
        text="/admin approve 123",
    )
    await dp.feed_update(bot, Update(update_id=2, message=approve_msg))

    assert any(c[0] == 123 and "доступ открыт" in c[1].lower() for c in calls)

    async with database.get_db() as db:
        cur = await db.execute("SELECT is_active FROM users WHERE tg_id=123")
        row = await cur.fetchone()
        assert row and row[0] == 1

    ping_msg = types.Message(
        message_id=3,
        date=datetime.now(),
        chat=types.Chat(id=123, type="private"),
        from_user=types.User(id=123, is_bot=False, first_name="User"),
        text="/ping",
    )
    await dp.feed_update(bot, Update(update_id=3, message=ping_msg))

    assert len(calls) == 5
    assert calls[-1][1] == "Bot ready"
