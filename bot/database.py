"""Database schema
=================

```
users(id PK, tg_id UNIQUE, name, is_active, requested_at)
requests(id PK, user_id FK users.id, prompt, model, created_at)
responses(id PK, request_id FK requests.id, content, created_at)
models(id PK, provider, name, updated_at)
```
"""

import os
import pathlib
from contextlib import asynccontextmanager

import aiosqlite

DB_PATH = pathlib.Path(os.getenv("DB_PATH", "/app/data/bot.db"))

CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users(
    id     INTEGER PRIMARY KEY,
    tg_id  INTEGER UNIQUE,
    name   TEXT,
    is_active INTEGER NOT NULL DEFAULT 0,
    requested_at TIMESTAMP
);
"""

CREATE_REQUESTS = """
CREATE TABLE IF NOT EXISTS requests(
    id         INTEGER PRIMARY KEY,
    user_id    INTEGER REFERENCES users(id),
    prompt     TEXT,
    model      TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_RESPONSES = """
CREATE TABLE IF NOT EXISTS responses(
    id         INTEGER PRIMARY KEY,
    request_id INTEGER REFERENCES requests(id),
    content    TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_MODELS = """
CREATE TABLE IF NOT EXISTS models(
    id         INTEGER PRIMARY KEY,
    provider   TEXT,
    name       TEXT,
    updated_at TIMESTAMP
);
"""

CREATE_FILES = """
CREATE TABLE IF NOT EXISTS files(
    id INTEGER PRIMARY KEY,
    request_id INTEGER REFERENCES requests(id) ON DELETE CASCADE,
    path TEXT,
    mime TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_CONFIG = """
CREATE TABLE IF NOT EXISTS config(
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


async def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys=ON")
        await db.execute(CREATE_USERS)
        await db.execute(CREATE_REQUESTS)
        await db.execute(CREATE_RESPONSES)
        await db.execute(CREATE_MODELS)
        await db.execute(CREATE_FILES)
        await db.execute(CREATE_CONFIG)
        await db.commit()


@asynccontextmanager
async def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(DB_PATH)
    await db.execute("PRAGMA foreign_keys=ON")
    try:
        yield db
    finally:
        await db.close()


async def log_request(user_id: int, prompt: str, model: str) -> int:
    async with get_db() as db:
        cur = await db.execute(
            "INSERT INTO requests(user_id, prompt, model) VALUES(?, ?, ?)",
            (user_id, prompt, model),
        )
        await db.commit()
        return cur.lastrowid


async def log_response(request_id: int, content: str) -> None:
    async with get_db() as db:
        await db.execute(
            "INSERT INTO responses(request_id, content) VALUES(?, ?)",
            (request_id, content),
        )
        await db.commit()


async def log_file(request_id: int, path: str, mime: str) -> None:
    async with get_db() as db:
        await db.execute(
            "INSERT INTO files(request_id, path, mime) VALUES(?, ?, ?)",
            (request_id, path, mime),
        )
        await db.commit()


async def model_exists(name: str) -> bool:
    async with get_db() as db:
        cur = await db.execute(
            "SELECT 1 FROM models WHERE name=? LIMIT 1",
            (name,),
        )
        row = await cur.fetchone()
        return row is not None


async def get_config(key: str, default: str | None = None) -> str | None:
    async with get_db() as db:
        query = "SELECT value FROM config WHERE key=?"
        cur = await db.execute(query, (key,))
        row = await cur.fetchone()
        return row[0] if row else default


async def set_config(key: str, value: str) -> None:
    async with get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO config(key, value) VALUES(?, ?)",
            (key, value),
        )
        await db.commit()
