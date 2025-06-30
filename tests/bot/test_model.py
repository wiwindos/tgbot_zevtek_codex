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
    monkeypatch.setenv("DEFAULT_MODEL", "gemini-pro")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture()
async def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "model.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    await database.init_db()
    return db_path


class DummyGemini:
    name = "gemini"
    supports_files = True
    calls = 0

    async def list_models(self):
        return ["gemini-pro"]

    async def generate(self, prompt, context=None, file=None):
        DummyGemini.calls += 1
        return "g"


class DummyMistral:
    name = "mistral"
    supports_files = False
    calls = 0

    async def list_models(self):
        return ["mistral-8x7b"]

    async def generate(self, prompt, context=None, file=None):
        DummyMistral.calls += 1
        return "m"


class DummyRegistry:
    def __init__(self):
        self._providers = {"gemini": DummyGemini(), "mistral": DummyMistral()}

    async def list_all(self):
        return ["gemini-pro", "mistral-8x7b"]

    def get(self, name, model=None):
        return self._providers[name]


@pytest.fixture()
def bot_and_dp(monkeypatch, temp_db):
    monkeypatch.setattr("services.llm_service.ProviderRegistry", DummyRegistry)
    monkeypatch.setattr("services.llm_service._registry", None)

    bot, dp = create_bot_and_dispatcher()

    # insert available models for validation
    async def _insert():
        async with database.get_db() as db:
            await db.execute(
                "INSERT INTO models(provider, name, updated_at) "
                "VALUES('m','mistral-8x7b','2024-01-01')"
            )
            await db.commit()

    asyncio.get_event_loop().run_until_complete(_insert())
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
async def test_model_persistence(bot_and_dp):
    bot, dp, calls = bot_and_dp
    chat_id = 1

    msg1 = types.Message(
        message_id=1,
        date=datetime.now(),
        chat=types.Chat(id=chat_id, type="private"),
        from_user=types.User(id=chat_id, is_bot=False, first_name="U"),
        text="hello",
    )
    await dp.feed_update(bot, Update(update_id=1, message=msg1))
    assert DummyGemini.calls == 1

    msg2 = types.Message(
        message_id=2,
        date=datetime.now(),
        chat=types.Chat(id=chat_id, type="private"),
        from_user=types.User(id=chat_id, is_bot=False, first_name="U"),
        text="/model mistral-8x7b",
    )
    await dp.feed_update(bot, Update(update_id=2, message=msg2))

    assert len(dp.context_buffer.get(chat_id)) > 0

    msg3 = types.Message(
        message_id=3,
        date=datetime.now(),
        chat=types.Chat(id=chat_id, type="private"),
        from_user=types.User(id=chat_id, is_bot=False, first_name="U"),
        text="next",
    )
    await dp.feed_update(bot, Update(update_id=3, message=msg3))

    assert DummyMistral.calls == 1
    assert DummyGemini.calls == 1
