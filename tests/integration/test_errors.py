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
    db_path = tmp_path / "errors.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    await database.init_db()
    return db_path


@pytest.fixture()
def bot_and_dp(monkeypatch, temp_db):
    bot, dp = create_bot_and_dispatcher()
    calls = []

    async def fake_send(self, chat_id, text, **kwargs):
        calls.append((chat_id, text))
        return types.Message(
            message_id=0,
            date=datetime.now(),
            chat=types.Chat(id=chat_id, type="private"),
            from_user=None,
            text=text,
        )

    monkeypatch.setattr(Bot, "send_message", fake_send)
    return bot, dp, calls


@pytest.mark.asyncio
async def test_graceful_error(bot_and_dp, monkeypatch, caplog):
    bot, dp, calls = bot_and_dp

    class BoomProvider:
        name = "gemini"

        async def list_models(self):
            return ["gemini-pro"]

        async def generate(self, prompt, context=None, file=None):
            raise RuntimeError("gemini boom")

    class BoomRegistry:
        def __init__(self):
            self._providers = {"gemini": BoomProvider()}

        async def list_all(self):
            return ["gemini-pro"]

        def get(self, name, model=None):
            return self._providers["gemini"]

    monkeypatch.setattr("services.llm_service.ProviderRegistry", BoomRegistry)
    monkeypatch.setattr("services.llm_service._registry", None)

    async with database.get_db() as db:
        await db.execute(
            "INSERT INTO users(tg_id, name, is_active) VALUES(?, ?, 1)",
            (123, "U"),
        )
        await db.commit()

    msg = types.Message(
        message_id=1,
        date=datetime.now(),
        chat=types.Chat(id=123, type="private"),
        from_user=types.User(id=123, is_bot=False, first_name="U"),
        text="hello",
    )
    await dp.feed_update(bot, Update(update_id=1, message=msg))

    assert any("попробуйте позже" in c[1].lower() for c in calls)
    assert any(c[0] == 999 and "RuntimeError" in c[1] for c in calls)
    messages = [r.getMessage() for r in caplog.records]
    assert any("unhandled_exception" in m for m in messages)
    assert any("RuntimeError" in m for m in messages)
