from aiogram import F, Router, types
from aiogram.filters import Command

from bot import database
from bot.utils import send_long_message
from scheduler.jobs import pull_and_sync_models
from services import user_service
from services.llm_service import get_registry


def get_admin_router(admin_chat_id: int) -> Router:
    router = Router()

    @router.message(F.from_user.id == admin_chat_id, Command("admin"))
    async def admin_commands(msg: types.Message) -> None:
        parts = msg.text.split()
        if len(parts) < 2 or parts[1] == "help":
            await send_long_message(
                msg.bot,
                msg.chat.id,
                (
                    "Используйте: stats, users pending, models, refresh "
                    "models, disable|enable <id>"
                ),
            )
            return

        cmd = parts[1]

        if cmd == "approve" and len(parts) == 3:
            tg_id = int(parts[2])
            await user_service.set_active(tg_id, True)
            await msg.answer("Пользователь активирован")
            await msg.bot.send_message(tg_id, "Доступ открыт")
        elif cmd == "users" and len(parts) >= 3 and parts[2] == "pending":
            pending = await user_service.pending_users()
            lines = [f"{u['tg_id']} — {u['name']}" for u in pending]
            text = "\n".join(lines) or "Нет заявок"
            await send_long_message(msg.bot, msg.chat.id, text, log=False)
        elif cmd == "stats":
            async with database.get_db() as db:
                query = "SELECT COUNT(*), SUM(is_active) FROM users"
                cur = await db.execute(query)
                users_total, active = await cur.fetchone()
                cur = await db.execute("SELECT COUNT(*) FROM requests")
                reqs = (await cur.fetchone())[0]
                cur = await db.execute("SELECT COUNT(*) FROM files")
                files = (await cur.fetchone())[0]
            text = (
                f"Users: {users_total} ({active} active) "
                f"• Requests: {reqs} • Files: {files}"
            )
            await msg.answer(text)
        elif cmd in {"disable", "enable"} and len(parts) == 3:
            tg_id = int(parts[2])
            await user_service.set_active(tg_id, cmd == "enable")
            if cmd == "enable":
                notify = "Доступ открыт"
            else:
                notify = "Доступ временно закрыт"
            await msg.bot.send_message(tg_id, notify)
            await msg.answer("Готово")
        elif cmd == "models":
            async with database.get_db() as db:
                cur = await db.execute(
                    "SELECT name, provider, updated_at FROM models "
                    "ORDER BY provider,name"
                )
                rows = await cur.fetchall()
            lines = [f"{r[1]}:{r[0]} — {r[2]}" for r in rows]
            text = "\n".join(lines) or "Нет моделей"
            await send_long_message(msg.bot, msg.chat.id, text, log=False)
        elif cmd == "refresh" and len(parts) >= 3 and parts[2] == "models":
            await pull_and_sync_models(get_registry())
            await msg.answer("Модели обновлены ☑️")

    @router.callback_query(F.from_user.id == admin_chat_id)
    async def approve_callback(cb: types.CallbackQuery) -> None:
        data = cb.data
        if data and data.startswith("approve:"):
            tg_id = int(data.split(":", 1)[1])
            await user_service.set_active(tg_id, True)
            await cb.message.answer("Пользователь активирован")
            await cb.bot.send_message(tg_id, "Доступ открыт")
            await cb.answer()

    return router
