"""Handlers for file uploads."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import aiofiles  # type: ignore
from aiogram import F, Router, types

from bot.utils import send_long_message
from services.llm_service import generate_reply, get_registry

FILES_DIR = Path(os.getenv("FILES_DIR", "./data/files"))
FILES_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_MODEL = "gemini-pro"


def get_file_router() -> Router:
    router = Router()

    @router.message(F.document)
    async def handle_document(msg: types.Message) -> None:
        assert msg.document
        info = await msg.bot.get_file(msg.document.file_id)
        ext = Path(info.file_path or msg.document.file_name or "").suffix
        dest = FILES_DIR / f"{uuid4().hex}{ext}"
        await msg.bot.download_file(info.file_path, dest)
        async with aiofiles.open(dest, "rb") as f:
            data = await f.read()
        registry = get_registry()
        provider = registry.get(DEFAULT_MODEL.split("-")[0])
        if not provider.supports_files:
            await send_long_message(
                msg.bot,
                msg.chat.id,
                "Эта модель не принимает файлы",
            )
            return
        reply = await generate_reply(
            msg.from_user.id,
            prompt="",
            model=DEFAULT_MODEL,
            file_bytes=data,
            file_path=str(dest),
            mime=msg.document.mime_type or "application/octet-stream",
        )
        await send_long_message(msg.bot, msg.chat.id, reply)

    return router
