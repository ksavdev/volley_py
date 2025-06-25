import datetime as dt
from src.utils.helpers import MINSK_TZ

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models import SessionLocal
from src.models.signup import Signup, SignupStatus
from src.models.announcement import Announcement
from src.models.user import User

from src.keyboards.my_signups import list_kb
from src.keyboards.back_cancel import back_cancel_kb
from src.utils.validators import MINSK_TZ
from aiogram.fsm.context import FSMContext
from src.states.signup_states import SignupStates
from src.handlers.start import whitelist_required
from src.services.rating import apply_penalty
from src.keyboards.manage_players import ManagePlayersCD

router = Router(name="my_signups")

# Маппинг статусов на русский
status_labels = {
    SignupStatus.pending:  "В ожидании",
    SignupStatus.accepted: "Принята",
    SignupStatus.declined: "Отклонена",
}

# ───────────── /requests — список моих заявок ────────────────
@router.message(Command("requests"))
@router.message(F.text == "📝 Мои заявки")
@whitelist_required
async def cmd_requests(msg: Message):
    user_id = msg.from_user.id
    async with SessionLocal() as s:
        signups = (
            await s.scalars(
                select(Signup)
                .options(
                    selectinload(Signup.announcement)
                        .selectinload(Announcement.hall)
                )
                .where(
                    Signup.player_id == user_id,
                    Signup.status.in_(["На рассмотрении", "Принята", "Отклонена"]),
                )
                .order_by(Signup.created_at)
            )
        ).all()

    if not signups:
        await msg.answer("У вас нет заявок.")
        return

    await msg.answer("Мои заявки:", reply_markup=list_kb(signups))

@router.callback_query(lambda cb: cb.data == "menu_requests")
@whitelist_required
async def cmd_requests_callback(cb: CallbackQuery):
    user_id = cb.from_user.id
    async with SessionLocal() as s:
        signups = (
            await s.scalars(
                select(Signup)
                .options(
                    selectinload(Signup.announcement)
                        .selectinload(Announcement.hall)
                )
                .where(
                    Signup.player_id == user_id,
                    Signup.status.in_(["На рассмотрении", "Принята", "Отклонена"]),
                )
                .order_by(Signup.created_at)
            )
        ).all()

    if not signups:
        await cb.message.answer("У вас нет заявок.")
        return

    await cb.message.answer("Мои заявки:", reply_markup=list_kb(signups))
    await cb.answer()


# ───────────── клик по заявке ────────────────────────────────
@router.callback_query(F.data.startswith("myreq_"))
@whitelist_required
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

    # --- Проверка времени до тренировки ---
    now = dt.datetime.now(MINSK_TZ)
    ann_dt = ann.datetime
    if ann_dt.tzinfo is None:
        # Assume stored as naive in local time, localize it
        ann_dt = MINSK_TZ.localize(ann_dt)
    # Now both are aware, safe to subtract
    time_left = (ann_dt - now).total_seconds() / 3600

    text = (
        f"ID заявки: {signup.id}\n"
        f"Зал: {ann.hall.name}\n"
        f"Дата/время: {ann.datetime.strftime('%d.%m %H:%M')}\n"
        f"Статус: {status_text}"
    )

    buttons = []
    if signup.status in (SignupStatus.pending, SignupStatus.accepted):
        if time_left > 5:
            buttons.append([
                InlineKeyboardButton(
                    text="🚫 Отменить заявку",
                    callback_data=f"cancel_{signup.id}"
                )
            ])
        else:
            buttons.append([
                InlineKeyboardButton(
                    text="Попросить удалить меня",
                    callback_data=f"ask_remove_{signup.id}"
                )
            ])
    # Удаляем кнопку "Назад"
    # buttons.append([
    #     InlineKeyboardButton(
    #         text="« Назад",
    #         callback_data="requests_back"
    #     )
    # ])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await cb.message.edit_text(text, reply_markup=kb)
    await cb.answer()


# ───────────── отмена заявки игроком ─────────────────────────
@router.callback_query(F.data.startswith("cancel_"))
@whitelist_required
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
        signup.comment = "cancelled_by_user"
        await s.commit()

    # уведомляем автора
    try:
        await cb.bot.send_message(
            signup.announcement.author_id,
            f"⛔️ Игрок отменил заявку на {signup.announcement.hall.name} "
            f"{signup.announcement.datetime.strftime('%d.%m %H:%M')}"
        )
    except Exception:
        pass

    # информируем игрока, стираем кнопки
    await cb.message.edit_text("Заявка отменена 🚫", reply_markup=None)
    await cb.answer()


# ───────────── Вернуться к списку заявок ─────────────────────
@router.callback_query(F.data == "requests_back")
@whitelist_required
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
@whitelist_required
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
    await state.update_data(comment=msg.text.strip())
    # ...дальнейшие шаги...

# --- Новый обработчик: запрос на удаление автору ---
@router.callback_query(F.data.startswith("ask_remove_"))
@whitelist_required
async def ask_remove(cb: CallbackQuery):
    signup_id = int(cb.data.split("_", 2)[2])
    async with SessionLocal() as s:
        signup = await s.get(
            Signup,
            signup_id,
            options=[
                selectinload(Signup.announcement).selectinload(Announcement.hall),
                selectinload(Signup.player)
            ],
        )
        if not signup or signup.player_id != cb.from_user.id:
            return await cb.answer("Заявка не найдена.", show_alert=True)
        ann = signup.announcement
        player = signup.player
        fio = player.fio or player.first_name
        # Отправить автору уведомление
        try:
            await cb.bot.send_message(
                ann.author_id,
                f"Игрок <a href='tg://user?id={player.id}'>{fio}</a> просит удалить его из тренировки "
                f"{ann.hall.name} {ann.datetime.strftime('%d.%m %H:%M')}.\n\n"
                "Если вы удалите игрока менее чем за 5 часов до тренировки, вы можете понизить его рейтинг на 1.00 балла.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Убрать игрока из тренировки",
                            callback_data=f"remove_player_{ann.id}_{player.id}"
                        )
                    ]
                ])
            )
        except Exception:
            pass
    await cb.message.edit_text(
        "Запрос на удаление отправлен автору тренировки.\n"
        "Если автор удалит вас менее чем за 5 часов до тренировки, он может понизить ваш рейтинг на 1.00 балла.",
        reply_markup=None
    )
    await cb.answer()


# --- Новый обработчик: автору предлагается выбор ---
@router.callback_query(F.data.startswith("remove_player_"))
@whitelist_required
async def remove_player_confirm(cb: CallbackQuery):
    # callback_data: remove_player_{ann_id}_{player_id}
    parts = cb.data.split("_")
    if len(parts) < 4:
        await cb.answer("Некорректные данные.", show_alert=True)
        return
    ann_id = int(parts[2])
    player_id = int(parts[3])

    async with SessionLocal() as s:
        signup = await s.scalar(
            select(Signup)
            .where(
                Signup.announcement_id == ann_id,
                Signup.player_id == player_id
            )
        )
        if not signup:
            await cb.answer("Заявка не найдена.", show_alert=True)
            return

    # Показываем автору выбор
    text = (
        "Вы действительно хотите удалить игрока из тренировки?\n"
        "Если удалите менее чем за 5 часов до тренировки, можете понизить рейтинг игрока на 1.00 балла."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Удалить",
                callback_data=ManagePlayersCD(signup_id=signup.id, penalty=0).pack()
            ),
            InlineKeyboardButton(
                text="Удалить и -1 к рейтингу",
                callback_data=ManagePlayersCD(signup_id=signup.id, penalty=1).pack()
            ),
        ]
    ])
    await cb.message.edit_text(text, reply_markup=kb)
    await cb.answer()


# --- Новый обработчик: действие удаления ---
@router.callback_query(ManagePlayersCD.filter())
@whitelist_required
async def do_remove_player(cb: CallbackQuery, state: FSMContext, callback_data: ManagePlayersCD):
    """
    Автор удаляет игрока (с возможным штрафом).
    """
    signup_id = int(callback_data.signup_id)
    penalty = bool(int(callback_data.penalty))

    async with SessionLocal() as session:
        signup: Signup = await session.get(Signup, signup_id, with_for_update=True)
        if not signup or signup.status == SignupStatus.declined:
            await cb.answer("Заявка уже закрыта.", show_alert=True)
            return

        signup.status = SignupStatus.declined
        await session.commit()

        # Сообщение в чат вместо алерта
        msg = "Игрок удалён, рейтинг понижен." if penalty else "Игрок удалён."
        await cb.message.answer(msg)

        if penalty:
            await apply_penalty(session, signup.player_id)

    # ...остальной ваш код (уведомления и т.д.)...