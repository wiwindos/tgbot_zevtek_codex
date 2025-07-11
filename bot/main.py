# bot/main.py
import argparse
import asyncio
import os

import structlog
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

from bot import __version__
from bot.admin import get_admin_router
from bot.context_middleware import ContextMiddleware
from bot.conversation import get_conversation_router
from bot.database import init_db
from bot.error_middleware import ErrorMiddleware
from bot.file_handlers import get_file_router
from bot.middleware import AuthMiddleware
from bot.utils import send_long_message
from logging_config import configure_logging
from providers.gemini import GeminiProvider
from scheduler.runner import configure, scheduler
from services.context import ContextBuffer
from services.llm_service import set_context_buffer

configure_logging()
logger = structlog.get_logger()

BOT_TOKEN = os.getenv("BOT_TOKEN")


async def start_handler(msg: types.Message):
    await send_long_message(
        msg.bot,
        msg.chat.id,
        "Привет! Это минимальный асинхронный бот 🐍\n"
        "Используйте /providers для выбора провайдера",
    )


HELP_TEXT = """\
Доступные команды:
/start — запуск бота
/help — это сообщение помощи
/providers — выбор провайдера
/models — выбор модели
Для обработки файлов выберите провайдера Gemini
Бот напомнит очистить контекст, если он станет слишком большим
"""

ADMIN_HELP = """\
/admin stats — статистика
/admin users pending — список заявок
/admin disable <id> — закрыть доступ
/admin enable <id> — вернуть доступ
/admin models — список моделей
/admin refresh models — обновить модели
"""


async def help_handler(msg: types.Message):
    text = HELP_TEXT
    admin_id = int(os.getenv("ADMIN_CHAT_ID", "0"))
    if msg.from_user.id == admin_id:
        text += "\n" + ADMIN_HELP
    await send_long_message(msg.bot, msg.chat.id, text)


async def ping_handler(msg: types.Message):
    await send_long_message(msg.bot, msg.chat.id, "Bot ready")


def create_bot_and_dispatcher():  # удобно реиспользовать в тестах
    token = os.getenv("BOT_TOKEN")
    admin_id = int(os.getenv("ADMIN_CHAT_ID", "0"))
    max_ctx = int(os.getenv("MAX_CONTEXT_MESSAGES", "20"))
    bot = Bot(token=token)
    dp = Dispatcher()
    buffer = ContextBuffer(max_messages=max_ctx)
    bot.context_buffer = buffer
    dp.context_buffer = buffer
    GeminiProvider()
    set_context_buffer(buffer)
    dp.message.middleware(ErrorMiddleware())
    dp.message.outer_middleware(ContextMiddleware(buffer))
    dp.message.middleware(AuthMiddleware(admin_id))
    dp.include_router(get_admin_router(admin_id))
    dp.include_router(get_file_router())
    dp.include_router(get_conversation_router(buffer))
    dp.message(Command("start"))(start_handler)
    dp.message(Command("help"))(help_handler)
    dp.message(Command("ping"))(ping_handler)
    if os.getenv("ENABLE_SCHEDULER", "1") == "1":
        configure()
        scheduler.start()
    return bot, dp


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ping", action="store_true", help="health check")
    args = parser.parse_args()

    load_dotenv()
    if args.ping:
        print("pong")
        return 0

    logger.info("bot_started", version=__version__)
    await init_db()  # Инициализация БД
    bot, dp = create_bot_and_dispatcher()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
