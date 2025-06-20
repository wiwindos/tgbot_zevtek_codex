# tests/test_smoke.py
import asyncio
from datetime import datetime

import pytest
from aiogram import types
from aiogram.types import Update

from bot.main import create_bot_and_dispatcher


@pytest.fixture(autouse=True)
def fake_token_env(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "123456:FAKE_TOKEN")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
def bot_and_dp(monkeypatch):
    bot, dp = create_bot_and_dispatcher()

    send_calls = []

    async def fake_answer(self, text, **kwargs):
        send_calls.append((self.chat.id, text))
        return types.Message(
            message_id=0,
            date=datetime.now(),
            chat=self.chat,
            from_user=self.from_user,
            text=text,
        )

    monkeypatch.setattr(types.Message, "answer", fake_answer)

    return bot, dp, send_calls


@pytest.mark.asyncio
async def test_ping_command(bot_and_dp):
    bot, dp, send_calls = bot_and_dp

    msg = types.Message(
        message_id=1,
        date=datetime.now(),
        chat=types.Chat(id=12345, type="private"),
        from_user=types.User(id=12345, is_bot=False, first_name="Tester"),
        text="/ping",
    )

    update = Update(update_id=1, message=msg)

    await dp.feed_update(bot, update)

    assert len(send_calls) == 1
    chat_id, text = send_calls[0]
    assert chat_id == 12345
    assert text == "Bot ready"
