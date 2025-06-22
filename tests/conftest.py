# tests/conftest.py
import sys
from pathlib import Path

import pytest

# ROOT — корень проекта, на уровень выше tests/
ROOT = Path(__file__).parent.parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def stub_provider_registry(monkeypatch):
    class DummyProvider:
        name = "gemini"

        async def list_models(self):
            return ["gemini-pro"]

        async def generate(self, prompt, context=None):
            return "stub"

    class DummyRegistry:
        def __init__(self):
            self._providers = {"gemini": DummyProvider()}

        async def list_all(self):
            return ["gemini-pro"]

        def get(self, name):
            return self._providers["gemini"]

    monkeypatch.setattr("services.llm_service.ProviderRegistry", DummyRegistry)
    monkeypatch.setenv("ENABLE_SCHEDULER", "0")
