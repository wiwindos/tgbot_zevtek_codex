# bot/main.py
import asyncio, os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start_handler(msg: types.Message):
    await msg.answer(
        "Привет! Это минимальный асинхронный бот 🐍",
        parse_mode=ParseMode.HTML,
    )

def create_bot_and_dispatcher():          # удобно реиспользовать в тестах
    #bot = Bot(token=BOT_TOKEN)
    token = os.getenv("BOT_TOKEN")
    bot = Bot(token=token)
    dp = Dispatcher()
    dp.message(Command("start"))(start_handler)
    return bot, dp

async def main():
    bot, dp = create_bot_and_dispatcher()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
