import asyncio
from datetime import datetime
from pathlib import Path

import aiofiles
import pytest
import pytest_asyncio
from aiogram import Bot, types
from aiogram.types import Update

from bot import database
from bot.main import create_bot_and_dispatcher
from bot.file_handlers import DEFAULT_MODEL, FILES_DIR
from providers import gemini, mistral


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture()
async def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "file.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    monkeypatch.setenv("FILES_DIR", str(tmp_path / "files"))
    monkeypatch.setenv("BOT_TOKEN", "123:TEST")
    await database.init_db()
    return db_path


@pytest.fixture()
def bot_and_dp(monkeypatch, temp_db):
    class DummyGemini(gemini.GeminiProvider):
        def __init__(self):
            pass

    class DummyMistral(mistral.MistralProvider):
        def __init__(self):
            pass

    class Reg:
        def __init__(self):
            self._providers = {
                "gemini": DummyGemini(),
                "mistral": DummyMistral(),
            }

        async def list_all(self):
            return ["gemini-pro"]

        def get(self, name):
            return self._providers[name]

    monkeypatch.setattr("services.llm_service.ProviderRegistry", Reg)
    monkeypatch.setattr("services.llm_service._registry", None, raising=False)
    bot, dp = create_bot_and_dispatcher()
    send_calls = []

    async def fake_answer(self, text, **kwargs):
        send_calls.append(text)
        return types.Message(
            message_id=0,
            date=datetime.now(),
            chat=self.chat,
            from_user=self.from_user,
            text=text,
        )

    async def fake_send(self, chat_id, text, **kwargs):
        send_calls.append(text)
        return types.Message(
            message_id=0,
            date=datetime.now(),
            chat=types.Chat(id=chat_id, type="private"),
            from_user=None,
            text=text,
        )

    async def fake_get_file(self, file_id):
        return types.File(file_id=file_id, file_unique_id="u", file_size=1, file_path="demo.pdf")

    async def fake_download(self, file_path, destination):
        async with aiofiles.open(destination, "wb") as f:
            await f.write(b"PDF")
        return None

    monkeypatch.setattr(types.Message, "answer", fake_answer)
    monkeypatch.setattr(Bot, "send_message", fake_send)
    monkeypatch.setattr(Bot, "get_file", fake_get_file)
    monkeypatch.setattr(Bot, "download_file", fake_download)

    return bot, dp, send_calls


@pytest.mark.asyncio
async def test_upload_and_log(bot_and_dp, monkeypatch):
    bot, dp, calls = bot_and_dp
    monkeypatch.setattr(gemini.GeminiProvider, "supports_files", True, raising=False)

    received = {}

    async def fake_generate(self, prompt, context=None, file_bytes=None):
        received["bytes"] = file_bytes
        return "ok"

    monkeypatch.setattr(gemini.GeminiProvider, "generate", fake_generate)

    msg = types.Message(
        message_id=1,
        date=datetime.now(),
        chat=types.Chat(id=1, type="private"),
        from_user=types.User(id=1, is_bot=False, first_name="u"),
        document=types.Document(file_id="123", file_unique_id="u1", file_name="demo.pdf", mime_type="application/pdf"),
    )
    await dp.feed_update(bot, Update(update_id=1, message=msg))

    assert received["bytes"] == b"PDF"
    files_path = Path(FILES_DIR)
    stored = list(files_path.glob("*.pdf"))
    assert stored
    async with database.get_db() as db:
        cur = await db.execute("SELECT mime FROM files")
        row = await cur.fetchone()
        assert row and row[0] == "application/pdf"


@pytest.mark.asyncio
async def test_model_without_support(bot_and_dp, monkeypatch):
    bot, dp, calls = bot_and_dp
    monkeypatch.setattr(mistral.MistralProvider, "supports_files", False, raising=False)
    monkeypatch.setattr(
        "bot.file_handlers.DEFAULT_MODEL", "mistral-small", raising=False
    )
    called = False

    async def fake_generate(self, prompt, context=None, file_bytes=None):
        nonlocal called
        called = True
        return "nope"

    monkeypatch.setattr(mistral.MistralProvider, "generate", fake_generate)

    msg = types.Message(
        message_id=1,
        date=datetime.now(),
        chat=types.Chat(id=2, type="private"),
        from_user=types.User(id=2, is_bot=False, first_name="u"),
        document=types.Document(file_id="321", file_unique_id="u2", file_name="bad.pdf", mime_type="application/pdf"),
    )
    await dp.feed_update(bot, Update(update_id=1, message=msg))

    assert any("не принимает" in c for c in calls)
    assert not called
