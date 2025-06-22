from aiogram import Router, types
from aiogram.filters import Command

from bot.utils import send_long_message
from services.context import ContextBuffer
from services.llm_service import generate_reply


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

    @router.message()
    async def dialog(message: types.Message) -> None:
        if message.text is None or message.text.startswith("/"):
            return
        reply = await generate_reply(
            message.from_user.id, message.text, model="gemini-pro"
        )
        await send_long_message(message.bot, message.chat.id, reply)

    return router
