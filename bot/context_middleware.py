from aiogram import BaseMiddleware, types

from services.context import ContextBuffer


class ContextMiddleware(BaseMiddleware):
    def __init__(self, buffer: ContextBuffer) -> None:
        super().__init__()
        self.buffer = buffer

    async def __call__(self, handler, event: types.TelegramObject, data):
        if isinstance(event, types.Message) and event.text is not None:
            self.buffer.add(event.chat.id, "user", event.text)
        result = await handler(event, data)
        return result
