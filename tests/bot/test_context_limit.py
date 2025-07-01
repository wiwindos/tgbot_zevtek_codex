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
    monkeypatch.setenv("ADMIN_CHAT_ID", "0")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture()
async def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "ctx.db"
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


def make_message(chat_id: int, text: str, i: int) -> types.Message:
    return types.Message(
        message_id=i,
        date=datetime.now(),
        chat=types.Chat(id=chat_id, type="private"),
        from_user=types.User(id=chat_id, is_bot=False, first_name="U"),
        text=text,
    )


@pytest.mark.asyncio
async def test_context_warning(bot_and_dp):
    bot, dp, calls = bot_and_dp
    chat_id = 303
    payload = "x" * 120

    for i in range(8):
        msg = make_message(chat_id, payload, i)
        await dp.feed_update(bot, Update(update_id=i, message=msg))
    assert not any("большой контекст" in c for c in calls)

    msg = make_message(chat_id, payload, 8)
    await dp.feed_update(bot, Update(update_id=8, message=msg))
    assert any("большой контекст" in c for c in calls)

    warn_count = sum("большой контекст" in c for c in calls)

    for i in range(9, 12):
        msg = make_message(chat_id, payload, i)
        await dp.feed_update(bot, Update(update_id=i, message=msg))
    assert sum("большой контекст" in c for c in calls) == warn_count

    cmd = make_message(chat_id, "/new", 12)
    await dp.feed_update(bot, Update(update_id=12, message=cmd))

    for i in range(13, 22):
        msg = make_message(chat_id, payload, i)
        await dp.feed_update(bot, Update(update_id=i, message=msg))
    assert sum("большой контекст" in c for c in calls) == warn_count + 1
