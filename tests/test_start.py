# tests/test_start.py

import asyncio
import pytest
from datetime import datetime
from aiogram import types
from aiogram.types import Update
from bot.main import create_bot_and_dispatcher

@pytest.fixture(autouse=True)
def fake_token_env(monkeypatch):
    # Валидный (но тестовый) токен
    monkeypatch.setenv("BOT_TOKEN", "123456:FAKE_TOKEN")

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture()
def bot_and_dp(monkeypatch):
    bot, dp = create_bot_and_dispatcher()

    # Перехватываем msg.answer вместо HTTP-запроса
    send_calls = []
    async def fake_answer(self, text, **kwargs):
        # self — это Message, у него .chat.id есть
        send_calls.append((self.chat.id, text))
        # возвращаем любой Message, у нас он не используется дальше
        return types.Message(
            message_id=0,
            date=datetime.now(),
            chat=self.chat,
            from_user=self.from_user,
            text=text,
        )

    # Мокаем метод на уровне класса so что всё, что вызывает Message.answer, попадёт сюда
    monkeypatch.setattr(types.Message, "answer", fake_answer)

    return bot, dp, send_calls

@pytest.mark.asyncio
async def test_start_command(bot_and_dp):
    bot, dp, send_calls = bot_and_dp

    # Синтезируем /start
    msg = types.Message(
        message_id=1,
        date=datetime.now(),
        chat=types.Chat(id=12345, type="private"),
        from_user=types.User(id=12345, is_bot=False, first_name="Tester"),
        text="/start",
    )

    # Оборачиваем в Update
    update = Update(update_id=1, message=msg)

    # Прокидываем в диспетчер
    await dp.feed_update(bot, update)

    # Проверяем, что fake_answer был вызван один раз
    assert len(send_calls) == 1
    chat_id, text = send_calls[0]
    assert chat_id == 12345
    assert "минимальный асинхронный бот" in text.lower()
