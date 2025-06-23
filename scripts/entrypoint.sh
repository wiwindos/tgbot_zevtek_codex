#!/bin/sh
set -e

python - <<'PY'
import asyncio
import pathlib
from bot import database

database.DB_PATH = pathlib.Path('data/bot.db')
asyncio.run(database.init_db())
PY

exec python -m bot.main
