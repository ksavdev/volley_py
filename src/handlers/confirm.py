from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import selectinload

from src.models import SessionLocal
from src.models.signup import Signup, SignupStatus
from src.models.announcement import Announcement
from src.models.user import User
from src.states.signup_states import DeclineStates
from src.utils.helpers import local

router = Router(name="confirm")


# ─────────────────────── ОБЩАЯ ЧАСТЬ ──────────────────────────
async def _load_signup(signup_id: int) -> Signup | None:
    async with SessionLocal() as s:
        return await s.get(
            Signup,
            signup_id,
            options=[
                selectinload(Signup.announcement)
                .selectinload(Announcement.hall)
            ],
        )


# ─────────────────────── ПРИНЯТЬ ✅ ───────────────────────────
@router.callback_query(F.data.startswith("acc_"))
async def accept_signup(cb: CallbackQuery):
    signup_id = int(cb.data.split("_")[1])
    signup = await _load_signup(signup_id)
    if not signup or signup.status != SignupStatus.pending:
        await cb.answer("Заявка уже обработана.", show_alert=True)
        return

    async with SessionLocal() as s:
        signup.status = SignupStatus.accepted
        await s.commit()
        hall = signup.announcement.hall.name
        dt   = local(signup.announcement.datetime).strftime("%d.%m %H:%M")

    # игроку
    await cb.bot.send_message(
        signup.player_id,
        f"✅ Ваша заявка на {hall} {dt} принята!"
    )
    # автору — квитанция
    await cb.bot.send_message(
        cb.from_user.id,
        f"Вы подтвердили игрока "
        f"<a href='tg://user?id={signup.player_id}'>ID {signup.player_id}</a> "
        f"на {hall} {dt}"
    )
    await cb.message.edit_reply_markup()
    await cb.answer("Игрок принят ✅")


# ─────────────────────── ОТКЛОНИТЬ ❌ (ШАГ 1) ─────────────────
@router.callback_query(F.data.startswith("dec_"))
async def decline_ask_reason(cb: CallbackQuery, state: FSMContext):
    signup_id = int(cb.data.split("_")[1])
    signup = await _load_signup(signup_id)
    if not signup or signup.status != SignupStatus.pending:
        await cb.answer("Заявка уже обработана.", show_alert=True)
        return

    await state.set_state(DeclineStates.waiting_reason)
    await state.update_data(signup_id=signup_id)
    await cb.message.answer("Укажите причину отказа:")
    await cb.answer()


# ─────────────────────── ОТКЛОНИТЬ ❌ (ШАГ 2) ─────────────────
@router.message(DeclineStates.waiting_reason)
async def decline_final(msg: Message, state: FSMContext):
    data = await state.get_data()
    signup_id: int = data["signup_id"]
    reason: str = msg.text.strip() or "—"
    signup = await _load_signup(signup_id)
    if not signup:
        await msg.answer("Заявка не найдена.")
        await state.clear()
        return

    async with SessionLocal() as s:
        signup.status = SignupStatus.declined
        await s.commit()
        hall = signup.announcement.hall.name
        dt   = local(signup.announcement.datetime).strftime("%d.%m %H:%M")

        # имя + рейтинг игрока
        db_user = await s.get(User, signup.player_id)
        rating  = f"{db_user.rating:.2f}" if db_user else "—"
        player_name = db_user.first_name if db_user else f"ID {signup.player_id}"

    # уведомляем игрока
    await msg.bot.send_message(
        signup.player_id,
        f"❌ Ваша заявка на {hall} {dt} отклонена.\nПричина: {reason}"
    )
    # квитанция автору
    await msg.answer(
        f"Вы отклонили {player_name} (⭐ {rating}).\nПричина: {reason}"
    )
    await state.clear()
