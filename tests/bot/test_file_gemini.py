import asyncio
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import aiofiles  # type: ignore
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
    monkeypatch.setenv("GEMINI_API_KEY", "x")


@pytest.fixture(autouse=True)
def stub_provider_registry(monkeypatch):
    monkeypatch.setenv("ENABLE_SCHEDULER", "0")
    monkeypatch.setattr("services.llm_service._registry", None, raising=False)
    yield


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture()
async def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "g.db"
    files_dir = tmp_path / "files"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    monkeypatch.setenv("FILES_DIR", str(files_dir))
    await database.init_db()
    return db_path, files_dir


@pytest.fixture()
def bot_and_dp(monkeypatch, temp_db):
    _, files_dir = temp_db

    def fake_generate_content(self, parts, stream=False):
        return SimpleNamespace(text=monkeypatch.context.get("ret", ""))

    monkeypatch.setattr(
        "google.generativeai.GenerativeModel.generate_content",
        fake_generate_content,
    )
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

    async def fake_get_file(self, file_id):
        return types.File(
            file_id=file_id,
            file_unique_id="u",
            file_path="cat.png",
        )

    async def fake_download(self, file_path, destination):
        async with aiofiles.open(destination, "wb") as f:
            data = Path("tests/fixtures/cat.png").read_bytes()
            await f.write(data)
        return destination

    monkeypatch.setattr(types.Message, "answer", fake_answer)
    monkeypatch.setattr(Bot, "send_message", fake_send)
    monkeypatch.setattr(Bot, "get_file", fake_get_file)
    monkeypatch.setattr(Bot, "download_file", fake_download)
    monkeypatch.context = {}
    return bot, dp, calls, files_dir, monkeypatch.context


@pytest.mark.asyncio
async def test_ok_image(bot_and_dp):
    bot, dp, calls, _, ctx = bot_and_dp
    ctx["ret"] = "image received"
    msg = types.Message(
        message_id=1,
        date=datetime.now(),
        chat=types.Chat(id=1, type="private"),
        from_user=types.User(id=1, is_bot=False, first_name="U"),
        document=types.Document(
            file_id="123",
            file_unique_id="u1",
            file_name="cat.png",
            mime_type="image/png",
            file_size=100,
        ),
    )

    await dp.feed_update(bot, Update(update_id=1, message=msg))
    assert any("image received" in c for c in calls)


@pytest.mark.asyncio
async def test_ok_audio(bot_and_dp, monkeypatch):
    bot, dp, calls, _, ctx = bot_and_dp
    ctx["ret"] = "audio received"

    async def fake_download(self, file_path, destination):
        async with aiofiles.open(destination, "wb") as f:
            data = Path("tests/fixtures/hello world.ogg").read_bytes()
            await f.write(data)
        return destination

    monkeypatch.setattr(Bot, "download_file", fake_download)

    msg = types.Message(
        message_id=2,
        date=datetime.now(),
        chat=types.Chat(id=2, type="private"),
        from_user=types.User(id=2, is_bot=False, first_name="U"),
        document=types.Document(
            file_id="456",
            file_unique_id="u2",
            file_name="hello.ogg",
            mime_type="audio/ogg",
            file_size=80,
        ),
    )
    await dp.feed_update(bot, Update(update_id=2, message=msg))
    assert any("audio received" in c for c in calls)


@pytest.mark.asyncio
async def test_too_big(bot_and_dp, monkeypatch, tmp_path):
    bot, dp, calls, files_dir, ctx = bot_and_dp
    big = tmp_path / "big.pdf"
    big.write_bytes(b"x" * 900_000)
    ctx["ret"] = "ignored"

    async def fake_download(self, file_path, destination):
        async with aiofiles.open(destination, "wb") as f:
            await f.write(big.read_bytes())
        return destination

    monkeypatch.setattr(Bot, "download_file", fake_download)
    msg = types.Message(
        message_id=3,
        date=datetime.now(),
        chat=types.Chat(id=3, type="private"),
        from_user=types.User(id=3, is_bot=False, first_name="U"),
        document=types.Document(
            file_id="789",
            file_unique_id="u3",
            file_name="big.pdf",
            mime_type="application/pdf",
            file_size=900000,
        ),
    )
    await dp.feed_update(bot, Update(update_id=3, message=msg))
    assert any("слишком велик" in c for c in calls)


@pytest.mark.asyncio
async def test_unsupported_on_deepseek(bot_and_dp, monkeypatch):
    bot, dp, calls, _, ctx = bot_and_dp
    ctx["ret"] = "ignored"
    dp.context_buffer.set_provider(4, "deepseek")
    dp.context_buffer.set_model(4, "deepseek-chat")

    msg = types.Message(
        message_id=4,
        date=datetime.now(),
        chat=types.Chat(id=4, type="private"),
        from_user=types.User(id=4, is_bot=False, first_name="U"),
        document=types.Document(
            file_id="111",
            file_unique_id="u4",
            file_name="cat.png",
            mime_type="image/png",
            file_size=100,
        ),
    )
    await dp.feed_update(bot, Update(update_id=4, message=msg))
    assert any("не принимает файлы" in c for c in calls)
