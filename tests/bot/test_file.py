import asyncio
from datetime import datetime
from pathlib import Path

import aiofiles  # type: ignore
import pytest
import pytest_asyncio
from aiogram import Bot, types
from aiogram.types import Update

from bot import database, file_handlers
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
    db_path = tmp_path / "files.db"
    files_dir = tmp_path / "files"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    monkeypatch.setenv("FILES_DIR", str(files_dir))
    await database.init_db()
    return db_path, files_dir


@pytest.fixture()
def bot_and_dp(monkeypatch, temp_db):
    _, files_dir = temp_db
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
            file_path="doc.pdf",
        )

    async def fake_download(self, file_path, destination):
        async with aiofiles.open(destination, "wb") as f:
            await f.write(b"pdf")
        return destination

    monkeypatch.setattr(types.Message, "answer", fake_answer)
    monkeypatch.setattr(Bot, "send_message", fake_send)
    monkeypatch.setattr(Bot, "get_file", fake_get_file)
    monkeypatch.setattr(Bot, "download_file", fake_download)

    return bot, dp, calls, files_dir


def setup_registry(monkeypatch, supports_files=True):
    class DummyGemini:
        name = "gemini"
        supports_files = True

        async def list_models(self):
            return ["gemini-pro"]

        async def generate(self, prompt, context=None, file_bytes=None):
            DummyGemini.captured = file_bytes
            return "ok"

    class DummyMistral:
        name = "mistral"
        supports_files = False

        async def list_models(self):
            return ["mistral-small"]

        async def generate(self, prompt, context=None, file_bytes=None):
            DummyMistral.captured = file_bytes
            return "ok"

    class DummyRegistry:
        def __init__(self):
            self._providers = {
                "gemini": DummyGemini(),
                "mistral": DummyMistral(),
            }

        async def list_all(self):
            return ["gemini-pro"]

        def get(self, name):
            return self._providers[name]

    monkeypatch.setattr("services.llm_service.ProviderRegistry", DummyRegistry)
    monkeypatch.setattr("services.llm_service._registry", None)
    DummyGemini.supports_files = supports_files
    return DummyGemini if supports_files else DummyMistral


@pytest.mark.asyncio
async def test_upload_and_store(bot_and_dp, monkeypatch):
    bot, dp, calls, files_dir = bot_and_dp
    provider = setup_registry(monkeypatch, supports_files=True)
    monkeypatch.setattr(file_handlers, "DEFAULT_MODEL", "gemini-pro")
    provider.captured = None

    msg = types.Message(
        message_id=1,
        date=datetime.now(),
        chat=types.Chat(id=1, type="private"),
        from_user=types.User(id=1, is_bot=False, first_name="U"),
        document=types.Document(
            file_id="123",
            file_unique_id="u1",
            file_name="demo.pdf",
            mime_type="application/pdf",
            file_size=3,
        ),
    )

    await dp.feed_update(bot, Update(update_id=1, message=msg))

    assert provider.captured == b"pdf"
    async with database.get_db() as db:
        cur = await db.execute("SELECT path, mime FROM files")
        row = await cur.fetchone()
        assert row and row[1] == "application/pdf"
        assert Path(row[0]).exists()

    assert "ok" in calls[-1]


@pytest.mark.asyncio
async def test_model_without_file_support(bot_and_dp, monkeypatch):
    bot, dp, calls, _ = bot_and_dp
    provider = setup_registry(monkeypatch, supports_files=False)
    provider.captured = None
    monkeypatch.setattr(file_handlers, "DEFAULT_MODEL", "mistral-small")

    msg = types.Message(
        message_id=1,
        date=datetime.now(),
        chat=types.Chat(id=2, type="private"),
        from_user=types.User(id=2, is_bot=False, first_name="U"),
        document=types.Document(
            file_id="222",
            file_unique_id="u2",
            file_name="demo.pdf",
            mime_type="application/pdf",
            file_size=3,
        ),
    )

    await dp.feed_update(bot, Update(update_id=1, message=msg))

    assert provider.captured is None
    assert any("не принимает файлы" in c for c in calls)
