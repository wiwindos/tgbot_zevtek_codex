import asyncio
from datetime import datetime

import httpx
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
    db_path = tmp_path / "proxy.db"
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
async def test_proxy_set(bot_and_dp):
    bot, dp, calls = bot_and_dp
    msg = types.Message(
        message_id=1,
        date=datetime.now(),
        chat=types.Chat(id=999, type="private"),
        from_user=types.User(id=999, is_bot=False, first_name="A"),
        text="/admin proxy set 191.102.181.223:9653:F8AaEo:rFkG",
    )
    await dp.feed_update(bot, Update(update_id=1, message=msg))


@pytest.mark.asyncio
async def test_proxy_check(bot_and_dp, monkeypatch):
    bot, dp, calls = bot_and_dp
    await database.set_config("GEMINI_PROXY", "10.0.0.1:8000")

    class DummyResp:
        status_code = 200

        def json(self):
            return {}

    class DummyClient:
        def __init__(self, *a, **kw):
            DummyClient.proxies = kw.get("proxies")

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def head(self, url):
            return DummyResp()

    monkeypatch.setattr(httpx, "AsyncClient", DummyClient)

    msg = types.Message(
        message_id=2,
        date=datetime.now(),
        chat=types.Chat(id=999, type="private"),
        from_user=types.User(id=999, is_bot=False, first_name="A"),
        text="/admin proxy check",
    )
    await dp.feed_update(bot, Update(update_id=2, message=msg))
