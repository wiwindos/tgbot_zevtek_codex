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
    db_path = tmp_path / "fb.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    await database.init_db()
    return db_path


class FailingProvider:
    name = "gemini"
    model = "gemini-pro"

    async def list_models(self):
        return [self.model]

    async def generate(self, prompt, context=None, file=None):
        raise httpx.TimeoutException("boom")


class OkProvider(FailingProvider):
    name = "deepseek"
    model = "deepseek-base"

    async def generate(self, prompt, context=None, file=None):
        return "ok"


class DummyRegistry:
    def __init__(self):
        self._providers = {
            "gemini": FailingProvider(),
            "deepseek": OkProvider(),
        }

    async def list_all(self):
        return ["gemini-pro", "deepseek-base"]

    def get(self, name, model=None):
        return self._providers[name]


@pytest.fixture()
def bot_and_dp(monkeypatch, temp_db):
    monkeypatch.setattr("services.llm_service.ProviderRegistry", DummyRegistry)
    monkeypatch.setattr("services.llm_service._registry", None, raising=False)
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

    async def fake_answer_cb(self, *args, **kwargs):
        calls.append("cb")
        return True

    async def fake_bot_call(self, method, timeout=None):
        calls.append("cb")
        return True

    monkeypatch.setattr(types.Message, "answer", fake_answer)
    monkeypatch.setattr(Bot, "send_message", fake_send)
    monkeypatch.setattr(Bot, "answer_callback_query", fake_answer_cb)
    monkeypatch.setattr(Bot, "__call__", fake_bot_call)
    return bot, dp, calls


@pytest.mark.asyncio
async def test_fallback_flow(bot_and_dp, caplog):
    bot, dp, calls = bot_and_dp

    async with database.get_db() as db:
        await db.execute(
            "INSERT INTO users(tg_id, name, is_active) VALUES(?, ?, 1)",
            (1, "U"),
        )
        await db.commit()

    msg = types.Message(
        message_id=1,
        date=datetime.now(),
        chat=types.Chat(id=1, type="private"),
        from_user=types.User(id=1, is_bot=False, first_name="U"),
        text="hi",
    )
    await dp.feed_update(bot, Update(update_id=1, message=msg))

    assert any("модели" in c.lower() for c in calls)
    assert any("provider_error" in r.getMessage() for r in caplog.records)
    assert dp.context_buffer.get(1) == [("user", "hi")]

    cb = types.CallbackQuery(
        id="1",
        from_user=types.User(id=1, is_bot=False, first_name="U"),
        chat_instance="x",
        data="show_models",
        message=types.Message(
            message_id=2,
            date=datetime.now(),
            chat=types.Chat(id=1, type="private"),
            from_user=None,
            text="btn",
        ),
    )
    await dp.feed_update(bot, Update(update_id=2, callback_query=cb))
    cb2 = types.CallbackQuery(
        id="2",
        from_user=types.User(id=1, is_bot=False, first_name="U"),
        chat_instance="x",
        data="model:deepseek-base",
        message=types.Message(
            message_id=3,
            date=datetime.now(),
            chat=types.Chat(id=1, type="private"),
            from_user=None,
            text="btn",
        ),
    )
    await dp.feed_update(bot, Update(update_id=3, callback_query=cb2))

    msg2 = types.Message(
        message_id=4,
        date=datetime.now(),
        chat=types.Chat(id=1, type="private"),
        from_user=types.User(id=1, is_bot=False, first_name="U"),
        text="again",
    )
    await dp.feed_update(bot, Update(update_id=4, message=msg2))

    assert any(c == "ok" for c in calls)

    admin = types.Message(
        message_id=5,
        date=datetime.now(),
        chat=types.Chat(id=999, type="private"),
        from_user=types.User(id=999, is_bot=False, first_name="A"),
        text="/admin errors",
    )
    await dp.feed_update(bot, Update(update_id=5, message=admin))

    assert any("TimeoutException" in c for c in calls)
