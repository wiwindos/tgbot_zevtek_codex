from __future__ import annotations

import os
import uuid
from pathlib import Path

import aiofiles  # type: ignore
from aiogram import Router, types

from bot.utils import send_long_message
from services.llm_service import generate_reply, get_registry

FILES_DIR = Path(os.getenv("FILES_DIR", "./data/files"))
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-pro")


def get_file_router() -> Router:
    FILES_DIR.mkdir(parents=True, exist_ok=True)
    router = Router()

    @router.message(lambda m: m.document or m.photo or m.audio)
    async def file_message(message: types.Message) -> None:
        doc = (
            message.document
            or (message.photo[-1] if message.photo else None)
            or message.audio
        )
        if doc is None:
            return
        registry = get_registry()
        provider = registry.get(DEFAULT_MODEL.split("-", 1)[0])
        if not provider.supports_files:
            await send_long_message(
                message.bot,
                message.chat.id,
                f"Модель {DEFAULT_MODEL} не принимает файлы",
            )
            return
        tg_file = await message.bot.get_file(doc.file_id)
        suffix = Path(doc.file_name or "file").suffix
        dest = FILES_DIR / f"{uuid.uuid4()}{suffix}"
        await message.bot.download_file(tg_file.file_path, dest)
        async with aiofiles.open(dest, "rb") as f:
            data = await f.read()
        reply = await generate_reply(
            message.from_user.id,
            "",
            DEFAULT_MODEL,
            file_bytes=data,
            file_path=str(dest),
            mime=getattr(doc, "mime_type", "application/octet-stream"),
        )
        await send_long_message(message.bot, message.chat.id, reply)

    return router
