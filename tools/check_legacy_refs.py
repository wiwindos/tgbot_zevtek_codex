import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {"tools", "scripts", "tests"}
fail = False
for path in ROOT.rglob("*"):
    if any(part in SKIP_DIRS or part.startswith(".") for part in path.parts):
        continue
    if path.name in {
        "IMPLEMENTATION_PLAN_11.md",
        "GENERAL_IMPLEMENTATION_PLAN.md",
    }:
        continue
    if path.suffix in {".py", ".md", ".env", ".example", ""}:
        try:
            text = path.read_text(errors="ignore")
        except (UnicodeDecodeError, IsADirectoryError):
            continue
        if "dipseek" in text.lower() or "gemini_proxy" in text.lower():
            print(f"Legacy reference found in {path}")
            fail = True
if fail:
    sys.exit(1)
