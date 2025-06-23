from __future__ import annotations

import os

import structlog
from aiogram import BaseMiddleware, types

from bot.utils import send_long_message

logger = structlog.get_logger()


class ErrorMiddleware(BaseMiddleware):
    """Catch unhandled exceptions and notify admin."""

    async def __call__(self, handler, event: types.TelegramObject, data):
        try:
            return await handler(event, data)
        except Exception as exc:  # noqa: BLE001
            logger.exception("unhandled_exception", exc_info=exc)
            if isinstance(event, types.Message):
                await send_long_message(
                    event.bot,
                    event.chat.id,
                    "Что-то пошло не так, попробуйте позже",
                )
            bot = data.get("bot")
            admin_id = int(os.getenv("ADMIN_CHAT_ID", "0"))
            if bot is not None and admin_id:
                await bot.send_message(admin_id, f"❗️ Ошибка: {exc!r}")
            return None
