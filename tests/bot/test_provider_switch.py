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
    db_path = tmp_path / "prov.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    await database.init_db()
    return db_path


class DummyProvider:
    def __init__(self, name: str, models: list[str]):
        self.name = name
        self.models = models

    async def list_models(self):
        return self.models

    async def generate(self, prompt, context=None, file_bytes=None):
        return self.name


class DummyRegistry:
    def __init__(self, mapping):
        self._providers = {
            name: DummyProvider(
                name,
                models,
            )
            for name, models in mapping.items()
        }

    async def list_all(self):
        names = []
        for models in self._providers.values():
            names.extend(models.models)
        return names

    def get(self, name, model=None):
        return self._providers[name]


AVAILABLE = {
    "deepseek": ["deepseek-base", "deepseek-large"],
    "mistral": ["mistral-small", "mistral-medium"],
    "gemini": ["gemini-pro", "gemini-1.5-pro"],
}


@pytest.fixture()
def bot_and_dp(monkeypatch, temp_db):
    monkeypatch.setattr(
        "services.llm_service.ProviderRegistry",
        lambda: DummyRegistry(AVAILABLE),
    )
    monkeypatch.setattr("services.llm_service._registry", None)

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

    async def fake_bot_call(self, method, timeout=None):
        calls.append("cb")
        return True

    monkeypatch.setattr(Bot, "__call__", fake_bot_call)

    async def fake_answer_cb(self, *args, **kwargs):
        calls.append("cb")
        return True

    monkeypatch.setattr(Bot, "answer_callback_query", fake_answer_cb)
    bot, dp = create_bot_and_dispatcher()
    return bot, dp, calls


@pytest.mark.asyncio
async def test_provider_switch(bot_and_dp):
    bot, dp, calls = bot_and_dp
    user_id = 101
    start = types.Message(
        message_id=0,
        date=datetime.now(),
        chat=types.Chat(id=user_id, type="private"),
        from_user=types.User(id=user_id, is_bot=False, first_name="U"),
        text="/start",
    )
    await dp.feed_update(bot, Update(update_id=0, message=start))
    msg = types.Message(
        message_id=1,
        date=datetime.now(),
        chat=types.Chat(id=user_id, type="private"),
        from_user=types.User(id=user_id, is_bot=False, first_name="U"),
        text="/providers",
    )
    await dp.feed_update(bot, Update(update_id=1, message=msg))
    assert calls
    cb = types.CallbackQuery(
        id="1",
        from_user=types.User(id=user_id, is_bot=False, first_name="U"),
        chat_instance="x",
        data="provider:mistral",
        message=types.Message(
            message_id=2,
            date=datetime.now(),
            chat=types.Chat(id=user_id, type="private"),
            from_user=None,
            text="btn",
        ),
    )
    await dp.feed_update(bot, Update(update_id=2, callback_query=cb))
    assert dp.context_buffer.user_provider[user_id] == "mistral"

    msg = types.Message(
        message_id=3,
        date=datetime.now(),
        chat=types.Chat(id=user_id, type="private"),
        from_user=types.User(id=user_id, is_bot=False, first_name="U"),
        text="/models",
    )
    await dp.feed_update(bot, Update(update_id=3, message=msg))
    assert calls
    cb2 = types.CallbackQuery(
        id="2",
        from_user=types.User(id=user_id, is_bot=False, first_name="U"),
        chat_instance="x",
        data="model:mistral-medium",
        message=types.Message(
            message_id=4,
            date=datetime.now(),
            chat=types.Chat(id=user_id, type="private"),
            from_user=None,
            text="btn",
        ),
    )
    await dp.feed_update(bot, Update(update_id=4, callback_query=cb2))
    # fmt: off
    assert (
        dp.context_buffer.user_models[user_id]["mistral"]
        == "mistral-medium"
    )
    # fmt: on

    msg = types.Message(
        message_id=5,
        date=datetime.now(),
        chat=types.Chat(id=user_id, type="private"),
        from_user=types.User(id=user_id, is_bot=False, first_name="U"),
        text="/providers",
    )
    await dp.feed_update(bot, Update(update_id=5, message=msg))
    cb3 = types.CallbackQuery(
        id="3",
        from_user=types.User(id=user_id, is_bot=False, first_name="U"),
        chat_instance="x",
        data="provider:gemini",
        message=types.Message(
            message_id=6,
            date=datetime.now(),
            chat=types.Chat(id=user_id, type="private"),
            from_user=None,
            text="btn",
        ),
    )
    await dp.feed_update(bot, Update(update_id=6, callback_query=cb3))
    assert dp.context_buffer.user_provider[user_id] == "gemini"

    msg = types.Message(
        message_id=7,
        date=datetime.now(),
        chat=types.Chat(id=user_id, type="private"),
        from_user=types.User(id=user_id, is_bot=False, first_name="U"),
        text="/providers",
    )
    await dp.feed_update(bot, Update(update_id=7, message=msg))
    cb4 = types.CallbackQuery(
        id="4",
        from_user=types.User(id=user_id, is_bot=False, first_name="U"),
        chat_instance="x",
        data="provider:mistral",
        message=types.Message(
            message_id=8,
            date=datetime.now(),
            chat=types.Chat(id=user_id, type="private"),
            from_user=None,
            text="btn",
        ),
    )
    await dp.feed_update(bot, Update(update_id=8, callback_query=cb4))
    # fmt: off
    assert (
        dp.context_buffer.user_models[user_id]["mistral"]
        == "mistral-medium"
    )
    # fmt: on


@pytest.mark.asyncio
async def test_model_does_not_change_provider(bot_and_dp):
    bot, dp, _ = bot_and_dp
    user_id = 102
    start = types.Message(
        message_id=0,
        date=datetime.now(),
        chat=types.Chat(id=user_id, type="private"),
        from_user=types.User(id=user_id, is_bot=False, first_name="U"),
        text="/start",
    )
    await dp.feed_update(bot, Update(update_id=0, message=start))
    msg = types.Message(
        message_id=1,
        date=datetime.now(),
        chat=types.Chat(id=user_id, type="private"),
        from_user=types.User(id=user_id, is_bot=False, first_name="U"),
        text="/providers",
    )
    await dp.feed_update(bot, Update(update_id=1, message=msg))
    cb = types.CallbackQuery(
        id="1",
        from_user=types.User(id=user_id, is_bot=False, first_name="U"),
        chat_instance="x",
        data="provider:gemini",
        message=types.Message(
            message_id=2,
            date=datetime.now(),
            chat=types.Chat(id=user_id, type="private"),
            from_user=None,
            text="btn",
        ),
    )
    await dp.feed_update(bot, Update(update_id=2, callback_query=cb))

    msg = types.Message(
        message_id=3,
        date=datetime.now(),
        chat=types.Chat(id=user_id, type="private"),
        from_user=types.User(id=user_id, is_bot=False, first_name="U"),
        text="/models",
    )
    await dp.feed_update(bot, Update(update_id=3, message=msg))
    cb2 = types.CallbackQuery(
        id="2",
        from_user=types.User(id=user_id, is_bot=False, first_name="U"),
        chat_instance="x",
        data="model:gemini-pro",
        message=types.Message(
            message_id=4,
            date=datetime.now(),
            chat=types.Chat(id=user_id, type="private"),
            from_user=None,
            text="btn",
        ),
    )
    await dp.feed_update(bot, Update(update_id=4, callback_query=cb2))
    assert dp.context_buffer.user_provider[user_id] == "gemini"
