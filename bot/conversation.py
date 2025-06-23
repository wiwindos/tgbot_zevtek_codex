from aiogram import Router, types
from aiogram.filters import Command

from bot.utils import send_long_message
from services.context import ContextBuffer
from services.llm_service import generate_reply, get_registry


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

    @router.message(Command("models"))
    async def list_models(msg: types.Message) -> None:
        registry = get_registry()
        models = await registry.list_all()
        text = "\n".join(models) or "Нет моделей"
        await send_long_message(msg.bot, msg.chat.id, text, log=False)

    @router.message(Command("model"))
    async def change_model(msg: types.Message) -> None:
        parts = msg.text.split(maxsplit=1)
        if len(parts) != 2:
            await msg.answer("Usage: /model <name>")
            return
        buffer.set_model(msg.from_user.id, parts[1])
        await msg.answer("Model updated ✅")

    @router.message()
    async def dialog(message: types.Message) -> None:
        if message.text is None or message.text.startswith("/"):
            return
        reply = await generate_reply(message.from_user.id, message.text)
        await send_long_message(message.bot, message.chat.id, reply)

    return router
