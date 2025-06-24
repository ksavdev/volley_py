from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select, func
from src.models import SessionLocal
from src.models.user import User
from src.models.signup import Signup, SignupStatus
from src.models.announcement import Announcement

router = Router(name="profile")

@router.message(Command("profile"))
async def cmd_profile(msg: Message):
    user_id = msg.from_user.id
    async with SessionLocal() as session:
        user = await session.get(User, user_id)
        if not user:
            await msg.answer("Профиль не найден.")
            return

        # Всего заявок
        total_signups = await session.scalar(
            select(func.count()).select_from(Signup).where(Signup.player_id == user_id)
        )
        # Принятые заявки
        accepted_signups = await session.scalar(
            select(func.count()).select_from(Signup).where(
                Signup.player_id == user_id,
                Signup.status == SignupStatus.accepted
            )
        )
        # Отклонённые заявки
        declined_signups = await session.scalar(
            select(func.count()).select_from(Signup).where(
                Signup.player_id == user_id,
                Signup.status == SignupStatus.declined
            )
        )
        # Создано объявлений
        total_ads = await session.scalar(
            select(func.count()).select_from(Announcement).where(Announcement.author_id == user_id)
        )
        # Сколько раз его тренировки были заполнены полностью
        full_ads = await session.scalar(
            select(func.count()).select_from(Announcement).where(
                Announcement.author_id == user_id,
                Announcement.players_need == 0
            )
        )
        # Количество оценок и рейтинг
        rating_votes = user.rating_votes
        rating = user.rating

    text = (
        f"👤 <b>Профиль</b>\n"
        f"Имя: {msg.from_user.full_name}\n"
        f"Username: @{msg.from_user.username or '-'}\n"
        f"ID: <code>{user_id}</code>\n\n"
        f"⭐️ Рейтинг: <b>{rating:.2f}</b> ({rating_votes} оценок)\n"
        f"📝 Всего заявок: <b>{total_signups}</b>\n"
        f"✅ Принято: <b>{accepted_signups}</b>\n"
        f"❌ Отклонено: <b>{declined_signups}</b>\n"
        f"📋 Создано объявлений: <b>{total_ads}</b>\n"
        f"🏆 Тренировок полностью заполнено: <b>{full_ads}</b>\n"
        f"🎯 Успешность: <b>{(accepted_signups/total_signups*100 if total_signups else 0):.0f}%</b>\n"
    )
    await msg.answer(text)