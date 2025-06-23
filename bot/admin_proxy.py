from __future__ import annotations

"""Router with proxy management commands."""

from aiogram import F, Router, types
from aiogram.filters import Command

from bot import database
from providers.gemini import GeminiProvider, ProxyError


def get_proxy_router(admin_chat_id: int, provider: GeminiProvider) -> Router:
    router = Router()

    @router.message(F.from_user.id == admin_chat_id, Command("admin"))
    async def proxy_commands(msg: types.Message) -> None:
        parts = msg.text.split()
        if len(parts) < 3 or parts[1] != "proxy":
            return

        if parts[2] == "set" and len(parts) == 4:
            await database.set_config("GEMINI_PROXY", parts[3])
            await provider.reload_settings()
            await msg.answer("Proxy saved ✅")
        elif parts[2] == "test":
            try:
                await provider.check_proxy()
            except ProxyError:
                await msg.answer("Proxy error ⛔")
            else:
                await msg.answer("Proxy alive 🟢")

    return router
