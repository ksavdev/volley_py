from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from src.states.rating_states import RatingStates
from src.keyboards.rating import rating_kb
from src.models import SessionLocal
from src.models.user import User
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.models.announcement import Announcement
from src.models.signup import Signup, SignupStatus
from src.utils.helpers import local
import datetime as dt

router = Router(name="rating")

@router.message(RatingStates.waiting_for_rating)
async def get_rating(msg: Message, state: FSMContext):
    if msg.text == "❌ Пропустить":
        await msg.answer("Спасибо! Оценка пропущена.")
        await state.clear()
        return
    if not msg.text.startswith("⭐️"):
        await msg.answer("Поставьте оценку от 1 до 5.", reply_markup=rating_kb())
        return
    try:
        rating = int(msg.text.replace("⭐️", "").strip())
        if not (1 <= rating <= 5):
            raise ValueError
    except Exception:
        await msg.answer("Поставьте оценку от 1 до 5.", reply_markup=rating_kb())
        return

    data = await state.get_data()
    user_id = data["rate_user_id"]
    async with SessionLocal() as session:
        user = await session.get(User, user_id)
        if user:
            user.rating_sum += rating
            user.rating_votes += 1
            user.rating = round(user.rating_sum / user.rating_votes, 2)
            await session.commit()
    await msg.answer("Спасибо за вашу оценку!")
    await state.clear()

async def send_rating_requests(bot):
    now = dt.datetime.now(local.tz)
    # Интервал для поиска: 2 часа назад ± 5 минут
    target_time = now - dt.timedelta(hours=2)
    interval_start = target_time - dt.timedelta(minutes=5)
    interval_end = target_time + dt.timedelta(minutes=5)
    async with SessionLocal() as session:
        anns = (await session.scalars(
            select(Announcement)
            .where(
                Announcement.datetime.between(interval_start, interval_end)
            )
            .options(selectinload(Announcement.signups))
        )).all()
        for ann in anns:
            for signup in ann.signups:
                if signup.status == SignupStatus.accepted:
                    await bot.send_message(
                        signup.player_id,
                        f"Тренировка {ann.hall.name} {local(ann.datetime).strftime('%d.%m %H:%M')} завершилась!\n\n"
                        "Пожалуйста, оцените организатора.",
                        reply_markup=rating_kb()
                    )
