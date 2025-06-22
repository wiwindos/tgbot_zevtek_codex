from aiogram import Router, types
from aiogram.filters import Command

from bot.utils import send_long_message
from services.context import ContextBuffer


def get_conversation_router(buffer: ContextBuffer) -> Router:
    router = Router()

    @router.message(Command(commands=["clear"]))
    async def clear_ctx(message: types.Message) -> None:
        buffer.clear(message.chat.id)
        await send_long_message(
            message.bot,
            message.chat.id,
            "Контекст очищен ✅",
            log=False,
        )

    return router
