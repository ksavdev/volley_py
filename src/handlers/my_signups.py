import datetime as dt
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models import SessionLocal
from src.models.signup import Signup, SignupStatus
from src.models.announcement import Announcement          # ← импорт
from src.keyboards.my_signups import list_kb, confirm_cancel_kb
from src.utils.helpers import MINSK_TZ, local

router = Router(name="my_signups")

# ───────────── /requests — список моих заявок ────────────────
@router.message(Command("requests"))
async def cmd_requests(msg: Message):
    async with SessionLocal() as s:
        signups = (
            await s.scalars(
                select(Signup)
                .options(
                    selectinload(Signup.announcement)              # 1-й hop
                    .selectinload(Announcement.hall)               # 2-й hop
                )
                .where(
                    Signup.player_id == msg.from_user.id,
                    Signup.status.in_(
                        [SignupStatus.pending, SignupStatus.accepted]
                    ),
                    Signup.announcement.has(
                        Announcement.datetime > dt.datetime.now(MINSK_TZ)
                    ),
                )
                .order_by(Signup.created_at)
            )
        ).all()

    await msg.answer("Мои заявки:", reply_markup=list_kb(signups))


# ───────────── клик по заявке ────────────────────────────────
@router.callback_query(F.data.startswith("myreq_"))
async def myreq_clicked(cb: CallbackQuery):
    signup_id = int(cb.data.split("_")[1])

    async with SessionLocal() as s:
        signup = await s.get(
            Signup,
            signup_id,
            options=[
                selectinload(Signup.announcement)
                .selectinload(Announcement.hall)
            ],
        )

    if not signup or signup.player_id != cb.from_user.id:
        await cb.answer("Заявка не найдена.", show_alert=True)
        return

    ann = signup.announcement
    text = (
        f"ID заявки: {signup.id}\n"
        f"Зал: {ann.hall.name}\n"
        f"Дата/время: {local(ann.datetime).strftime('%d.%m %H:%M')}\n"
        f"Статус: {signup.status.name}"
    )
    await cb.message.edit_text(text, reply_markup=confirm_cancel_kb(signup.id))
    await cb.answer()


# ───────────── отмена заявки игроком ─────────────────────────
@router.callback_query(F.data.startswith("cancel_"))
async def cancel_signup(cb: CallbackQuery):
    signup_id = int(cb.data.split("_")[1])

    async with SessionLocal() as s:
        signup = await s.get(
            Signup,
            signup_id,
            options=[
                selectinload(Signup.announcement)
                .selectinload(Announcement.hall)
            ],
        )
        if not signup or signup.player_id != cb.from_user.id:
            await cb.answer("Заявка не найдена.", show_alert=True)
            return
        if signup.status == SignupStatus.declined:
            await cb.answer("Заявка уже отклонена.", show_alert=True)
            return

        signup.status = SignupStatus.declined
        await s.commit()

    # уведомление автору (не зависим от сессии)
    try:
        await cb.bot.send_message(
            signup.announcement.author_id,
            f"⛔️ Игрок отменил заявку на {signup.announcement.hall.name} "
            f"{local(signup.announcement.datetime).strftime('%d.%m %H:%M')}"
        )
    except Exception:
        pass

    await cb.message.edit_text("Заявка отменена 🚫")
    await cb.answer()
