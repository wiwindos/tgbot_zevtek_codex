import asyncio
from typing import Any

import pytest
import pytest_asyncio

from bot import database
from providers.gemini import GeminiProvider


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture()
async def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "gemini.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    await database.init_db()
    return db_path


@pytest.mark.asyncio
async def test_proxy_applied(monkeypatch, temp_db):
    monkeypatch.setenv("GEMINI_API_KEY", "dummy")
    monkeypatch.setenv("GEMINI_PROXY", "http://191.102.181.223:9653")

    captured: dict[str, Any] = {}

    class DummyModel:
        def generate_content(self, messages):
            captured["messages"] = messages
            return type("R", (), {"text": "ok"})()

    def dummy_config(**kw):
        captured["proxy"] = kw.get("proxy")

    monkeypatch.setattr("google.generativeai.configure", dummy_config)
    monkeypatch.setattr(
        "google.generativeai.GenerativeModel", lambda name: DummyModel()
    )

    provider = GeminiProvider()
    await provider.generate("hi")

    assert captured["proxy"] == "http://191.102.181.223:9653"


@pytest.mark.asyncio
async def test_model_switch_keeps_ctx(monkeypatch, temp_db):
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    monkeypatch.setenv("DEFAULT_MODEL", "mistral-8x7b")

    # dummy provider with counter
    texts = []

    class DummyModel:
        def generate_content(self, messages):
            texts.append(messages[-1]["parts"][0])
            return type("R", (), {"text": "reply"})()

    monkeypatch.setattr("google.generativeai.configure", lambda **kw: None)
    monkeypatch.setattr(
        "google.generativeai.GenerativeModel", lambda name: DummyModel()
    )

    provider = GeminiProvider()
    # chat history
    await provider.generate("one")
    await provider.generate("two")
    await provider.reload_settings()  # switch to gemini via command
    await provider.generate("three")

    assert texts == ["one", "two", "three"]


@pytest.mark.asyncio
async def test_admin_proxy_commands(monkeypatch, temp_db):
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    provider = GeminiProvider()

    monkeypatch.setattr("google.generativeai.configure", lambda **kw: None)
    monkeypatch.setattr(
        "google.generativeai.GenerativeModel", lambda name: provider._client
    )

    await database.set_config("GEMINI_PROXY", "http://1.1.1.1:8080")
    await provider.reload_settings()

    class DummyResp:
        status_code = 204

    class DummyClient:
        def __init__(self, *a, **kw):
            DummyClient.proxies = kw.get("proxies")

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def head(self, url):
            return DummyResp()

    monkeypatch.setattr("httpx.AsyncClient", DummyClient)

    await provider.check_proxy()
    assert DummyClient.proxies == {"https": "http://1.1.1.1:8080"}
