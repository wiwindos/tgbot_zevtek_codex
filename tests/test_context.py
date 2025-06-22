import asyncio
from datetime import datetime

import pytest
import pytest_asyncio
from aiogram import Bot, types
from aiogram.types import Update

from bot import database
from bot.main import create_bot_and_dispatcher
from bot.utils import send_long_message


@pytest.fixture(autouse=True)
def fake_env(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "123:TEST")
    monkeypatch.setenv("ADMIN_CHAT_ID", "0")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture()
async def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "context.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    await database.init_db()
    return db_path


@pytest.fixture()
def bot_and_dp(monkeypatch, temp_db):
    bot, dp = create_bot_and_dispatcher()

    calls = []

    async def fake_answer(self, text, **kwargs):
        calls.append(text)
        return types.Message(
            message_id=0,
            date=datetime.now(),
            chat=self.chat,
            from_user=self.from_user,
            text=text,
        )

    async def fake_send(self, chat_id, text, **kwargs):
        calls.append(text)
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
async def test_history(bot_and_dp):
    bot, dp, calls = bot_and_dp
    chat_id = 12345
    for i, text in enumerate(["one", "two", "three"], start=1):
        msg = types.Message(
            message_id=i,
            date=datetime.now(),
            chat=types.Chat(id=chat_id, type="private"),
            from_user=types.User(id=chat_id, is_bot=False, first_name="User"),
            text=text,
        )
        await dp.feed_update(bot, Update(update_id=i, message=msg))

    buffer = dp.context_buffer
    assert len(buffer.get(chat_id)) == 3


@pytest.mark.asyncio
async def test_clear_command(bot_and_dp):
    bot, dp, calls = bot_and_dp
    chat_id = 1
    msg = types.Message(
        message_id=1,
        date=datetime.now(),
        chat=types.Chat(id=chat_id, type="private"),
        from_user=types.User(id=chat_id, is_bot=False, first_name="User"),
        text="/clear",
    )
    await dp.feed_update(bot, Update(update_id=1, message=msg))

    buffer = dp.context_buffer
    assert len(buffer.get(chat_id)) == 0
    assert any("Контекст очищен" in t for t in calls)


@pytest.mark.asyncio
async def test_split_long_message(bot_and_dp):
    bot, dp, calls = bot_and_dp
    long_text = "x" * 6000
    await send_long_message(bot, 2, long_text)
    assert len(calls) == 2
    assert "".join(calls) == long_text
