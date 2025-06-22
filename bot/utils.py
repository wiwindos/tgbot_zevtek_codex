import textwrap

from aiogram import Bot


async def send_long_message(
    bot: Bot, chat_id: int, text: str, *, log: bool = True
) -> None:
    """Split messages longer than 4096 characters and send sequentially."""
    chunks = textwrap.wrap(text, width=4096)
    for chunk in chunks:
        await bot.send_message(chat_id, chunk)
    if log and hasattr(bot, "context_buffer"):
        bot.context_buffer.add(chat_id, "assistant", text)
