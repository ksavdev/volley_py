import asyncio
from aiogram import Bot
from aiogram.client.bot import DefaultBotProperties
from src.config import BOT_TOKEN
from src.handlers.rating import send_rating_requests

async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    try:
        await send_rating_requests(bot)
    except Exception as e:
        print(f"send_rating_requests error: {e}")
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())