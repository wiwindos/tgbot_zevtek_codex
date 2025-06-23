#!/bin/sh
set -e
python - <<'PY'
import asyncio
from bot import database
asyncio.run(database.init_db())
PY
exec python -m bot.main

