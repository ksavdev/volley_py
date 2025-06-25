from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select, func
from src.models import SessionLocal
from src.models.user import User
from src.models.signup import Signup, SignupStatus
from src.models.announcement import Announcement
import datetime as dt

router = Router(name="profile")

@router.message(Command("profile"))
@router.callback_query(lambda c: c.data == "menu_profile")
async def cmd_profile(event):
    # event может быть Message или CallbackQuery
    if isinstance(event, Message):
        user_id = event.from_user.id
        send = event.answer
        full_name = event.from_user.full_name
        username = event.from_user.username
    else:
        user_id = event.from_user.id
        send = event.message.answer
        full_name = event.from_user.full_name
        username = event.from_user.username

    async with SessionLocal() as session:
        user = await session.get(User, user_id)
        if not user:
            await send("Профиль не найден.")
            if hasattr(event, "answer"):
                await event.answer()
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
        now = dt.datetime.now().replace(tzinfo=None)
        full_ads = await session.scalar(
            select(func.count()).select_from(Announcement).where(
                Announcement.author_id == user_id,
                Announcement.datetime <= now,
                # Например: тренировка прошла и заявок столько же, сколько capacity
                Announcement.capacity == (
                    select(func.count())
                    .select_from(Signup)
                    .where(
                        Signup.announcement_id == Announcement.id,
                        Signup.status == SignupStatus.accepted
                    ).scalar_subquery()
                )
            )
        )
        # Количество оценок и рейтинг
        rating_votes = user.rating_votes
        rating = user.rating

    fio = user.fio or full_name
    phone = user.phone or "-"
    text = (
        f"👤 <b>Профиль</b>\n"
        f"ФИО: {fio}\n"
        f"Телефон: {phone}\n"
        f"Username: @{username or '-'}\n"
        f"ID: <code>{user_id}</code>\n\n"
        f"⭐️ Рейтинг: <b>{rating:.2f}</b> ({rating_votes} оценок)\n"
        f"📝 Всего заявок: <b>{total_signups}</b>\n"
        f"✅ Принято: <b>{accepted_signups}</b>\n"
        f"❌ Отклонено: <b>{declined_signups}</b>\n"
        f"📋 Создано объявлений: <b>{total_ads}</b>\n"
        f"🏆 Тренировок полностью заполнено: <b>{full_ads}</b>\n"
        f"🎯 Успешность: <b>{(accepted_signups/total_signups*100 if total_signups else 0):.0f}%</b>\n"
    )
    await send(text)
    if hasattr(event, "answer"):
        await event.answer()