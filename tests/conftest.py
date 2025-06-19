# tests/conftest.py
import sys
from pathlib import Path

# ROOT — корень проекта, на уровень выше tests/
ROOT = Path(__file__).parent.parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
