"""Database schema
=================

```
users(id PK, tg_id UNIQUE, name, is_active, requested_at)
requests(id PK, user_id FK users.id, prompt, model, created_at)
responses(id PK, request_id FK requests.id, content, created_at)
models(id PK, provider, name, updated_at)
```
"""

import pathlib
from contextlib import asynccontextmanager

import aiosqlite

DB_PATH = pathlib.Path("bot.db")

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


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys=ON")
        await db.execute(CREATE_USERS)
        await db.execute(CREATE_REQUESTS)
        await db.execute(CREATE_RESPONSES)
        await db.execute(CREATE_MODELS)
        await db.execute(CREATE_FILES)
        await db.commit()


@asynccontextmanager
async def get_db():
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
