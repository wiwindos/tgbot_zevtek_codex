# bot/main.py
import argparse
import asyncio
import os

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from dotenv import load_dotenv

from bot.admin import get_admin_router
from bot.middleware import AuthMiddleware

BOT_TOKEN = os.getenv("BOT_TOKEN")


async def start_handler(msg: types.Message):
    await msg.answer(
        "Привет! Это минимальный асинхронный бот 🐍",
        parse_mode=ParseMode.HTML,
    )


HELP_TEXT = """\
Доступные команды:
/start — запуск бота
/help — это сообщение помощи
"""


async def help_handler(msg: types.Message):
    await msg.answer(HELP_TEXT)


async def ping_handler(msg: types.Message):
    await msg.answer("Bot ready")


def create_bot_and_dispatcher():  # удобно реиспользовать в тестах
    token = os.getenv("BOT_TOKEN")
    admin_id = int(os.getenv("ADMIN_CHAT_ID", "0"))
    bot = Bot(token=token)
    dp = Dispatcher()
    dp.message.middleware(AuthMiddleware(admin_id))
    dp.include_router(get_admin_router(admin_id))
    dp.message(Command("start"))(start_handler)
    dp.message(Command("help"))(help_handler)
    dp.message(Command("ping"))(ping_handler)
    return bot, dp


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ping", action="store_true", help="health check")
    args = parser.parse_args()

    if args.ping:
        load_dotenv()
        print("pong")
        return 0

    bot, dp = create_bot_and_dispatcher()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
