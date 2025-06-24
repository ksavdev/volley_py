from decimal import Decimal
from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, BotCommand
from aiogram import Bot
from src.config import ADMINS
from src.models import SessionLocal
from src.models.user import User
from src.keyboards.main_menu import main_menu_kb

router = Router()

@router.message(CommandStart())
async def on_start(message: Message):
    tg_user = message.from_user
    tg_id = tg_user.id
    username = tg_user.username
    first_name = tg_user.first_name or ""
    last_name = tg_user.last_name

    async with SessionLocal() as session:
        db_user = await session.get(User, tg_id)
        if db_user is None:
            user = User(
                id=tg_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                rating_sum=0,
                rating_votes=0,
                rating=Decimal("5.00"),
            )
            session.add(user)
            await session.commit()
        else:
            # обновляем имя/username если изменились
            db_user.username = username
            db_user.first_name = first_name
            db_user.last_name = last_name
            await session.commit()

    text = (
        f"👋 Привет, {first_name or 'игрок'}!\n\n"
        "Я помогу найти или создать тренировку по волейболу в Минске.\n"
        "Выберите действие из меню ниже 👇"
    )
    await message.answer(text, reply_markup=main_menu_kb(tg_id))

@router.message(Command("start"))
async def cmd_start(msg: Message, bot: Bot):
    if msg.from_user.id in ADMINS:
        await bot.set_my_commands([
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="new", description="Создать объявление"),
            BotCommand(command="my", description="Мои объявления"),
            BotCommand(command="search", description="Найти тренировку"),
            BotCommand(command="requests", description="Мои заявки"),
            BotCommand(command="addhall", description="Добавить зал"),
            BotCommand(command="dm", description="Писать пользователю"),
        ], scope={"type": "chat", "chat_id": msg.from_user.id})
    else:
        await bot.set_my_commands([
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="new", description="Создать объявление"),
            BotCommand(command="my", description="Мои объявления"),
            BotCommand(command="search", description="Найти тренировку"),
            BotCommand(command="requests", description="Мои заявки"),
        ], scope={"type": "chat", "chat_id": msg.from_user.id})
