from aiogram import Router, types
from aiogram.filters import Command

from services import user_service


def get_admin_router(admin_chat_id: int) -> Router:
    router = Router()

    async def approve_cmd(msg: types.Message):
        parts = msg.text.split()
        if len(parts) == 3 and parts[1] == "approve":
            tg_id = int(parts[2])
            await user_service.set_active(tg_id, True)
            await msg.answer("Пользователь активирован")
            await msg.bot.send_message(tg_id, "Доступ открыт")

    async def pending_cmd(msg: types.Message):
        pending = await user_service.pending_users()
        lines = [f"{u['tg_id']} — {u['name']}" for u in pending]
        text = "\n".join(lines) or "Нет заявок"
        await msg.answer(text)

    router.message.filter(lambda m: m.chat.id == admin_chat_id)
    router.message(Command("admin"))(approve_cmd)
    router.message(Command("admin"))(pending_cmd)

    async def approve_callback(cb: types.CallbackQuery):
        data = cb.data
        if data and data.startswith("approve:"):
            tg_id = int(data.split(":", 1)[1])
            await user_service.set_active(tg_id, True)
            await cb.message.answer("Пользователь активирован")
            await cb.bot.send_message(tg_id, "Доступ открыт")
            await cb.answer()

    router.callback_query(approve_callback)

    return router
