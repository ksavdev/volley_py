import datetime as dt

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models import SessionLocal
from src.models.signup import Signup, SignupStatus
from src.models.announcement import Announcement
from src.keyboards.my_signups import list_kb
from src.keyboards.back_cancel import back_cancel_kb
from src.utils.helpers import MINSK_TZ, local
from aiogram.fsm.context import FSMContext
from src.states.signup_states import SignupStates

router = Router(name="my_signups")

# Маппинг статусов на русский
status_labels = {
    SignupStatus.pending:  "В ожидании",
    SignupStatus.accepted: "Принята",
    SignupStatus.declined: "Отклонена",
}

# ───────────── /requests — список моих заявок ────────────────
@router.message(Command("requests"))
async def cmd_requests(msg: Message):
    async with SessionLocal() as s:
        signups = (
            await s.scalars(
                select(Signup)
                .options(
                    selectinload(Signup.announcement)
                        .selectinload(Announcement.hall)
                )
                .where(
                    Signup.player_id == msg.from_user.id,
                    Signup.status.in_([
                        SignupStatus.pending,
                        SignupStatus.accepted,
                        SignupStatus.declined
                    ]),
                    # Уберите или закомментируйте фильтр по дате, если хотите видеть все заявки:
                    # Signup.announcement.has(
                    #     Announcement.datetime > dt.datetime.now(MINSK_TZ)
                    # ),
                )
                .order_by(Signup.created_at)
            )
        ).all()

    if not signups:
        return await msg.answer("У вас нет активных заявок.")

    await msg.answer("Мои заявки:", reply_markup=list_kb(signups))


# ───────────── клик по заявке ────────────────────────────────
@router.callback_query(F.data.startswith("myreq_"))
async def myreq_clicked(cb: CallbackQuery):
    signup_id = int(cb.data.split("_", 1)[1])

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
        return await cb.answer("Заявка не найдена.", show_alert=True)

    ann = signup.announcement
    status_text = status_labels.get(signup.status, signup.status.name)

    text = (
        f"ID заявки: {signup.id}\n"
        f"Зал: {ann.hall.name}\n"
        f"Дата/время: {local(ann.datetime).strftime('%d.%m %H:%M')}\n"
        f"Статус: {status_text}"
    )

    # Составляем клавиатуру: отменить (только если pending/accepted) + «Назад»
    buttons = []
    if signup.status in (SignupStatus.pending, SignupStatus.accepted):
        buttons.append([
            InlineKeyboardButton(
                text="🚫 Отменить заявку",
                callback_data=f"cancel_{signup.id}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(
            text="« Назад",
            callback_data="requests_back"
        )
    ])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await cb.message.edit_text(text, reply_markup=kb)
    await cb.answer()


# ───────────── отмена заявки игроком ─────────────────────────
@router.callback_query(F.data.startswith("cancel_"))
async def cancel_signup(cb: CallbackQuery):
    signup_id = int(cb.data.split("_", 1)[1])

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
            return await cb.answer("Заявка не найдена.", show_alert=True)
        if signup.status == SignupStatus.declined:
            return await cb.answer("Заявка уже отклонена.", show_alert=True)

        # переводим статус в отклонённый
        signup.status = SignupStatus.declined
        # возвращаем слот обратно в объявлении
        signup.announcement.players_need += 1

        await s.commit()

    # уведомляем автора
    try:
        await cb.bot.send_message(
            signup.announcement.author_id,
            f"⛔️ Игрок отменил заявку на {signup.announcement.hall.name} "
            f"{local(signup.announcement.datetime).strftime('%d.%m %H:%M')}"
        )
    except Exception:
        pass

    # информируем игрока, стираем кнопки
    await cb.message.edit_text("Заявка отменена 🚫", reply_markup=None)
    await cb.answer()


# ───────────── Вернуться к списку заявок ─────────────────────
@router.callback_query(F.data == "requests_back")
async def requests_back(cb: CallbackQuery):
    async with SessionLocal() as s:
        signups = (
            await s.scalars(
                select(Signup)
                .options(
                    selectinload(Signup.announcement)
                        .selectinload(Announcement.hall)
                )
                .where(
                    Signup.player_id == cb.from_user.id,
                    Signup.status.in_([
                        SignupStatus.pending,
                        SignupStatus.accepted,
                        SignupStatus.declined
                    ]),
                )
                .order_by(Signup.created_at)
            )
        ).all()

    if not signups:
        await cb.message.edit_text("У вас нет активных заявок.", reply_markup=None)
    else:
        await cb.message.edit_text("Мои заявки:", reply_markup=list_kb(signups))
    await cb.answer()


@router.message(SignupStates.waiting_for_comment)
async def signup_comment_step(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await msg.answer("Заявка отменена.", reply_markup=None)
        await state.clear()
        return
    if msg.text == "⬅️ Назад":
        await msg.answer("Выберите объявление для заявки.", reply_markup=None)
        await state.set_state(SignupStates.waiting_for_announcement)
        return
    await state.update_data(comment=msg.text.strip())
    # ...дальнейшие шаги...
