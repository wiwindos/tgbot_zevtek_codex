from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot import database
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

    @router.message(Command("providers"))
    async def choose_provider(msg: types.Message) -> None:
        buttons = [
            [
                InlineKeyboardButton(
                    text="Deepseek",
                    callback_data="provider:deepseek",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Mistral",
                    callback_data="provider:mistral",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Gemini",
                    callback_data="provider:gemini",
                )
            ],
        ]
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await msg.answer("Выберите провайдера:", reply_markup=kb)

    @router.callback_query(lambda c: c.data and c.data.startswith("provider:"))
    async def provider_callback(cb: types.CallbackQuery) -> None:
        prov = cb.data.split(":", 1)[1]
        buffer.set_provider(cb.from_user.id, prov)
        registry = get_registry()
        models = await registry.get(prov).list_models()
        saved = buffer.user_models.get(cb.from_user.id, {}).get(prov)
        if saved:
            buffer.set_model(cb.from_user.id, saved)
        elif models:
            buffer.set_model(cb.from_user.id, models[0])
        await cb.answer(f"Провайдер переключён на {prov.capitalize()}")
        await cb.message.edit_text(f"Провайдер: {prov}")

    @router.message(Command("models"))
    async def list_models(msg: types.Message) -> None:
        prov = buffer.get_provider(msg.from_user.id)
        if prov is None:
            await msg.answer("Сначала выберите /providers")
            return
        registry = get_registry()
        models = await registry.get(prov).list_models()
        buttons = [
            [
                InlineKeyboardButton(
                    text=m,
                    callback_data=f"model:{m}",
                )
            ]
            for m in models
        ]
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await msg.answer("Модели:", reply_markup=kb)

    @router.message(Command("model"))
    async def change_model(msg: types.Message) -> None:
        parts = msg.text.split(maxsplit=1)
        if len(parts) != 2:
            await msg.answer("Usage: /model <name>")
            return
        name = parts[1]
        if not await database.model_exists(name):
            await msg.answer("Unknown model")
            return
        buffer.set_model(msg.from_user.id, name)
        buffer.set_provider(msg.from_user.id, name.split("-", 1)[0])
        await msg.answer(f"Model switched to {name}")

    @router.callback_query(lambda c: c.data and c.data.startswith("model:"))
    async def model_callback(cb: types.CallbackQuery) -> None:
        name = cb.data.split(":", 1)[1]
        buffer.set_model(cb.from_user.id, name)
        buffer.set_provider(cb.from_user.id, name.split("-", 1)[0])
        await cb.answer(f"Модель {name} активна")
        await cb.message.edit_text(f"Модель: {name}")

    @router.message()
    async def dialog(message: types.Message) -> None:
        if message.text is None or message.text.startswith("/"):
            return
        reply = await generate_reply(message.from_user.id, message.text)
        await send_long_message(message.bot, message.chat.id, reply)

    return router
