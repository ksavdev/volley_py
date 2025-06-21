from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from src.models import SessionLocal
from src.models.user import User

router = Router()

@router.message(CommandStart())
async def on_start(message: Message):
    tg_id      = message.from_user.id
    username   = message.from_user.username
    full_name  = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()

    async with SessionLocal() as session:
        db_user = await session.get(User, tg_id)
        if db_user is None:
            session.add(User(id=tg_id, username=username, full_name=full_name))
            await session.commit()
        await message.answer(
            "👋 Привет! Этот бот поможет найти волейбольную тренировку или собрать игроков.\n"
            "Основное меню появится позже во время разработки."
        )
