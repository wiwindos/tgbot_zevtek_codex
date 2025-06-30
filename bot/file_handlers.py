"""Handlers for file uploads."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import aiofiles  # type: ignore
import structlog
from aiogram import F, Router, types

from bot.utils import send_long_message
from services.file_service import FileTooLarge, UnsupportedMime, detect_mime
from services.llm_service import generate_reply, get_registry

FILES_DIR = Path(os.getenv("FILES_DIR", "./data/files"))
FILES_DIR.mkdir(parents=True, exist_ok=True)
logger = structlog.get_logger()

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-2.0-flash")


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
        try:
            payload = detect_mime(data, dest.name)
        except FileTooLarge:
            await send_long_message(
                msg.bot, msg.chat.id, "Файл слишком велик (≤ 512 kB)."
            )
            return
        except UnsupportedMime:
            await send_long_message(
                msg.bot, msg.chat.id, "Неподдерживаемый формат файла"
            )
            return
        registry = get_registry()
        selected = msg.bot.context_buffer.get_model(msg.from_user.id)
        model = selected or DEFAULT_MODEL
        provider = registry.get(model.split("-")[0])
        logger.info(
            "file_received",
            kind=payload.kind.value,
            size=len(data),
            mime=payload.mime,
            provider=provider.name,
            model=model,
            user_id=msg.from_user.id,
        )
        if not (
            provider.supports_files
            and getattr(provider, f"supports_{payload.kind.value}", False)
        ):
            await send_long_message(
                msg.bot,
                msg.chat.id,
                "Эта модель не принимает файлы",
            )
            return
        reply = await generate_reply(
            msg.from_user.id,
            prompt="",
            model=model,
            file=payload,
            file_path=str(dest),
            mime=payload.mime,
        )
        await send_long_message(msg.bot, msg.chat.id, reply)

    return router
