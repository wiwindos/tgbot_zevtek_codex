# bot/main.py
import argparse
import asyncio
import os

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from dotenv import load_dotenv


async def start_handler(msg: types.Message):
    await msg.answer(
        "Привет! Это минимальный асинхронный бот 🐍",
        parse_mode=ParseMode.HTML,
    )


async def help_handler(msg: types.Message):
    await msg.answer(
        """Доступные команды:
/start — запуск бота
/help — это сообщение помощи"""
    )


async def ping_handler(msg: types.Message):
    await msg.answer("Bot ready")


def create_bot_and_dispatcher():  # удобно реиспользовать в тестах
    token = os.getenv("BOT_TOKEN")
    bot = Bot(token=token)
    dp = Dispatcher()
    dp.message(Command("start"))(start_handler)
    dp.message(Command("help"))(help_handler)
    dp.message(Command("ping"))(ping_handler)
    return bot, dp


async def main():
    bot, dp = create_bot_and_dispatcher()
    await dp.start_polling(bot)


def cli(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ping", action="store_true")
    args = parser.parse_args(argv)
    load_dotenv()
    if args.ping:
        print("pong")
        return 0
    asyncio.run(main())
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
