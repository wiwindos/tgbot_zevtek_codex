# tests/conftest.py
import os
import subprocess
import sys
from pathlib import Path

import pytest

# ROOT — корень проекта, на уровень выше tests/
ROOT = Path(__file__).parent.parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "docker: tests that require local Docker daemon",
    )


def pytest_collection_modifyitems(config, items):
    ci = os.getenv("CI", "0") == "1"
    try:
        daemon_up = (
            subprocess.call(
                ["docker", "info"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            == 0
        )
    except FileNotFoundError:
        daemon_up = False
    if ci or not daemon_up:
        skip_it = pytest.mark.skip(
            reason="Docker tests skipped on CI or when daemon is absent"
        )
        for item in items:
            if "docker" in item.keywords:
                item.add_marker(skip_it)


@pytest.fixture(autouse=True)
def stub_provider_registry(monkeypatch):
    class DummyProvider:
        name = "gemini"

        async def list_models(self):
            return ["gemini-2.0-flash"]

        async def generate(self, prompt, context=None, file_bytes=None):
            return "stub"

    class DummyRegistry:
        def __init__(self):
            self._providers = {"gemini": DummyProvider()}

        async def list_all(self):
            return ["gemini-pro"]

        def get(self, name, model=None):
            return self._providers["gemini"]

    monkeypatch.setattr("services.llm_service.ProviderRegistry", DummyRegistry)
    monkeypatch.setenv("ENABLE_SCHEDULER", "0")
