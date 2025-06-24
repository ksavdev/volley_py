import asyncio
from aiogram import Bot
from src.config import BOT_TOKEN
from src.handlers.rating import send_rating_requests

async def main():
    bot = Bot(token=BOT_TOKEN)
    await send_rating_requests(bot)
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())