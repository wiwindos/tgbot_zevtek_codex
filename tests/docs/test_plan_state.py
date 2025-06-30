from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]


@pytest.mark.parametrize(
    "path",
    [
        ROOT / "README.md",
        *list((ROOT / "docs").glob("*.md")),
    ],
)
def test_no_legacy_refs(path: Path):
    text = path.read_text(encoding="utf-8").lower()
    assert "dipseek" not in text


@pytest.mark.parametrize("path", list(ROOT.glob("**/*.py")))
def test_no_legacy_code(path: Path):
    if (
        "__pycache__" in path.parts
        or {"tools", "scripts"} & set(path.parts)
        or path.name in {"test_migration_deepseek.py", "test_plan_state.py"}
    ):
        pytest.skip()
    text = path.read_text(encoding="utf-8").lower()
    assert "dipseek" not in text


def test_env_example():
    text = (ROOT / ".env.example").read_text()
    assert "DIPSEEK_" not in text
