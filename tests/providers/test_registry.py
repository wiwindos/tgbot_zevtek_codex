import asyncio

import pytest
import pytest_asyncio
import respx

from bot import database
from providers import ProviderRegistry
from services.llm_service import generate_reply


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture()
async def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "providers.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    await database.init_db()
    return db_path


@pytest.mark.asyncio
async def test_list_models_aggregate(monkeypatch):
    async def fake_gemini(self):
        return ["gemini-pro"]

    monkeypatch.setattr(
        "providers.gemini.GeminiProvider.__init__",
        lambda self: None,
    )

    monkeypatch.setattr(
        "providers.gemini.GeminiProvider.list_models",
        fake_gemini,
    )
    monkeypatch.setenv("MISTRAL_API_KEY", "x")
    monkeypatch.setenv("DIPSEEK_API_KEY", "y")
    monkeypatch.setenv("DIPSEEK_ENDPOINT", "https://dipseek.ai")

    with respx.mock(assert_all_called=False) as router:
        router.get("https://api.mistral.ai/v1/models").respond(
            200, json={"data": [{"id": "mistral-8x7b"}]}
        )
        router.get("https://dipseek.ai/v1/models").respond(
            200, json={"models": ["dipseek-latest"]}
        )
        registry = ProviderRegistry()
        models = await registry.list_all()

    assert set(models) == {
        "gemini-pro",
        "mistral-8x7b",
        "dipseek-latest",
    }


@pytest.mark.asyncio
async def test_generate_logs_db(monkeypatch, temp_db):
    async def fake_generate(self, prompt, context=None):
        return "stub"

    monkeypatch.setattr(
        "providers.gemini.GeminiProvider.generate",
        fake_generate,
    )

    async with database.get_db() as db:
        await db.execute(
            "INSERT INTO users(tg_id, name) VALUES(?, ?)",
            (1, "u"),
        )
        await db.commit()

    response = await generate_reply(1, "hi", model="gemini-pro")
    assert response == "stub"

    async with database.get_db() as db:
        cur = await db.execute("SELECT model FROM requests")
        row = await cur.fetchone()
        assert row and row[0] == "gemini-pro"
        cur = await db.execute("SELECT content FROM responses")
        row = await cur.fetchone()
        assert row and row[0] == "stub"
