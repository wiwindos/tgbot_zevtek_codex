import asyncio
from datetime import datetime

import pytest
import pytest_asyncio
from aiogram import Bot, types

from bot import database
from providers import dipseek, gemini, mistral
from providers import registry as reg
from scheduler.jobs import pull_and_sync_models


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture()
async def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "refresh.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    monkeypatch.setenv("BOT_TOKEN", "123:TEST")
    monkeypatch.setenv("ADMIN_CHAT_ID", "1")
    await database.init_db()
    return db_path


@pytest.fixture()
def provider_registry(monkeypatch):
    monkeypatch.setattr(gemini.GeminiProvider, "__init__", lambda self: None)

    async def g_models(self):
        return ["g-1"]

    monkeypatch.setattr(gemini.GeminiProvider, "list_models", g_models)
    monkeypatch.setattr(mistral.MistralProvider, "__init__", lambda self: None)

    async def m_models(self):
        return ["m-1"]

    monkeypatch.setattr(mistral.MistralProvider, "list_models", m_models)
    monkeypatch.setattr(dipseek.DipseekProvider, "__init__", lambda self: None)

    async def d_models(self):
        return ["d-1"]

    monkeypatch.setattr(dipseek.DipseekProvider, "list_models", d_models)
    return reg.ProviderRegistry()


@pytest.fixture()
def send_calls(monkeypatch):
    calls = []

    async def fake_send(self, chat_id, text, **kwargs):
        calls.append(text)
        return types.Message(
            message_id=0,
            date=datetime.now(),
            chat=types.Chat(id=chat_id, type="private"),
            from_user=None,
            text=text,
        )

    monkeypatch.setattr(Bot, "send_message", fake_send)
    return calls


@pytest.mark.asyncio
async def test_initial_fill(temp_db, provider_registry, send_calls):
    await pull_and_sync_models(provider_registry)
    async with database.get_db() as db:
        cur = await db.execute("SELECT COUNT(*) FROM models")
        count = (await cur.fetchone())[0]
    assert count == 3
    assert len(send_calls) == 0


@pytest.mark.asyncio
async def test_detect_changes(
    temp_db,
    provider_registry,
    monkeypatch,
    send_calls,
):
    await pull_and_sync_models(provider_registry)

    async def m2_models(self):
        return ["m-2"]

    monkeypatch.setattr(mistral.MistralProvider, "list_models", m2_models)
    await pull_and_sync_models(provider_registry)
    async with database.get_db() as db:
        query = "SELECT name FROM models WHERE provider='mistral'"
        cur = await db.execute(query)
        names = {row[0] for row in await cur.fetchall()}
    assert names == {"m-1", "m-2"}
    assert len(send_calls) == 1
    assert "m-2" in send_calls[0]
