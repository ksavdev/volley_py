import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.config import BOT_TOKEN, settings
from src.handlers import router as main_router
from src.handlers.rating import send_rating_requests

# Импортируем Base и engine для автоматического создания таблиц
from src.models.base import Base, engine
import traceback


async def on_startup(bot: Bot):
    # При старте создаём в БД все таблицы, которых ещё нет
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Таблицы созданы (если их не было)")
    print("Бот запущен успешно")


async def periodic_ratings(bot):
    try:
        await send_rating_requests(bot)
    except Exception as e:
        print("Exception in periodic_ratings job:")
        traceback.print_exc()


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
        BotCommand(command="profile", description="Мой профиль"),  # ← добавить сюда
    ])

    # Настраиваем диспетчер с хранилищем состояний в памяти
    dp = Dispatcher(storage=MemoryStorage())

    # Подключаем основной роутер с обработчиками
    dp.include_router(main_router)

    # Регистрируем функцию on_startup
    dp.startup.register(on_startup)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        periodic_ratings,
        "interval",
        minutes=5,
        args=[bot],
        max_instances=1,
        misfire_grace_time=60,
    )
    scheduler.start()

    try:
        # Запускаем поллинг
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await engine.dispose()  # Грейсфул shutdown
        # При завершении закрываем сессию бота
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
