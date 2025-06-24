import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from src.config import BOT_TOKEN, settings
from src.handlers import router as main_router


async def on_startup(bot: Bot):
    print("Бот запущен успешно")

async def main() -> None:
    # ↓ передаём parse_mode через DefaultBotProperties
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    
    
    )

    await bot.set_my_commands([
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="new", description="Создать объявление"),
        BotCommand(command="my", description="Мои объявления"),
        BotCommand(command="search", description="Найти тренировку"),
        BotCommand(command="requests", description="Мои заявки"),
        BotCommand(command="addhall", description="Добавить зал"),
        BotCommand(command="dm", description="Писать пользователю"),
    ])
    dp = Dispatcher(storage=MemoryStorage())
    
    dp.include_router(main_router)
    dp.startup.register(on_startup)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
