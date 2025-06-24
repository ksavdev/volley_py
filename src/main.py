import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from src.config import BOT_TOKEN, settings
from src.handlers import router as main_router

# Импортируем Base и engine для автоматического создания таблиц
from src.models.base import Base, engine


async def on_startup(bot: Bot):
    # При старте создаём в БД все таблицы, которых ещё нет
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Таблицы созданы (если их не было)")
    print("Бот запущен успешно")


async def main() -> None:
    # Инициализируем бота с HTML-парсингом
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )

    # Регистрируем команды бота в меню
    await bot.set_my_commands([
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="new", description="Создать объявление"),
        BotCommand(command="my", description="Мои объявления"),
        BotCommand(command="search", description="Найти тренировку"),
        BotCommand(command="requests", description="Мои заявки"),
    ])

    # Настраиваем диспетчер с хранилищем состояний в памяти
    dp = Dispatcher(storage=MemoryStorage())

    # Подключаем основной роутер с обработчиками
    dp.include_router(main_router)

    # Регистрируем функцию on_startup
    dp.startup.register(on_startup)

    try:
        # Запускаем поллинг
        await dp.start_polling(bot)
    finally:
        # При завершении закрываем сессию бота
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
