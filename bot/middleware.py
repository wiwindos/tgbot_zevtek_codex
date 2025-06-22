from aiogram import BaseMiddleware, Bot, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from services import user_service


class AuthMiddleware(BaseMiddleware):
    def __init__(self, admin_chat_id: int) -> None:
        super().__init__()
        self.admin_chat_id = admin_chat_id

    async def __call__(self, handler, event: types.TelegramObject, data):
        if isinstance(event, types.Message):
            tg_id = event.from_user.id
            name = event.from_user.full_name
            user = await user_service.get_or_create_user(tg_id, name)

            if tg_id == self.admin_chat_id:
                return await handler(event, data)

            if self.admin_chat_id == 0:
                if not user["is_active"]:
                    await user_service.set_active(tg_id, True)
                return await handler(event, data)

            if not user["is_active"]:
                if event.text and event.text.startswith("/start"):
                    await event.answer("Ваша заявка отправлена администратору")
                    button = InlineKeyboardButton(
                        text="✅ Одобрить",
                        callback_data=f"approve:{tg_id}",
                    )
                    markup = InlineKeyboardMarkup(inline_keyboard=[[button]])
                    bot: Bot = data["bot"]
                    await bot.send_message(
                        self.admin_chat_id,
                        f"Новая заявка от {name} ({tg_id})",
                        reply_markup=markup,
                    )
                return  # block further handling until approved
        return await handler(event, data)
