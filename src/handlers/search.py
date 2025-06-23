# src/handlers/search.py

import datetime as dt

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models import SessionLocal
from src.models.announcement import Announcement
from src.models.signup import Signup, SignupStatus
from src.states.signup_states import SignupStates
from src.keyboards.search_menu import search_menu_kb
from src.keyboards.ad_list import ad_list_kb
from src.keyboards.signup_request import signup_kb
from src.utils.validators import MINSK_TZ
from src.utils.helpers import local
from src.handlers.request_notify import notify_author

router = Router(name="search")


@router.message(Command("search"))
async def cmd_search(msg: Message):
    """
    Шаг 1: выбор платных / бесплатных тренировок.
    """
    await msg.answer(
        "Выберите тип тренировки:",
        reply_markup=search_menu_kb()
    )


@router.callback_query(F.data.in_({"search_paid", "search_free"}))
async def choose_type(cb: CallbackQuery):
    """
    Шаг 2: список будущих объявлений выбранного типа.
    """
    is_paid = (cb.data == "search_paid")
    now     = dt.datetime.now(MINSK_TZ)

    async with SessionLocal() as session:
        ads = (
            await session.scalars(
                select(Announcement)
                .options(
                    selectinload(Announcement.hall),
                    selectinload(Announcement.signups)
                )
                .where(
                    Announcement.is_paid   == is_paid,
                    Announcement.datetime  > now,
                )
                .order_by(Announcement.datetime)
            )
        ).all()

    if not ads:
        await cb.answer("Ничего не найдено.", show_alert=True)
        return

    await cb.message.edit_text(
        "Доступные тренировки:",
        reply_markup=ad_list_kb(ads)
    )
    await cb.answer()


@router.callback_query(F.data == "search_menu")
async def back_to_search_menu(cb: CallbackQuery):
    """
    Возврат на выбор платных/бесплатных.
    """
    await cb.message.edit_text(
        "Выберите тип тренировки:",
        reply_markup=search_menu_kb()
    )
    await cb.answer()


@router.callback_query(F.data.startswith("ad_"))
async def ad_chosen(cb: CallbackQuery, state: FSMContext):
    """
    Шаг 3: подробная карточка тренировки + кнопки «Записаться» / «Назад».
    Показывает зал, адрес, дату, слоты и принятых игроков.
    """
    ad_id = int(cb.data.split("_", 1)[1])
    now   = dt.datetime.now(MINSK_TZ)

    # — загружаем объявление вместе с hall и signups->player
    async with SessionLocal() as session:
        result = await session.execute(
            select(Announcement)
            .options(
                selectinload(Announcement.hall),
                selectinload(Announcement.signups)
                    .selectinload(Signup.player),
            )
            .where(Announcement.id == ad_id)
        )
        ad = result.scalar_one_or_none()

    if not ad:
        return await cb.answer("Объявление не найдено.", show_alert=True)

    # — проверяем, что тренировка ещё не прошла
    if ad.datetime <= now:
        return await cb.answer("К сожалению, эта тренировка уже прошла.", show_alert=True)

    # — считаем занятые слоты и список игроков
    accepted = [s for s in ad.signups if s.status == SignupStatus.accepted]
    total_slots = ad.players_need
    taken_slots = len(accepted)
        # ← НОВЫЙ БЛОК: если все слоты заняты
    if taken_slots >= total_slots:
        # Показываем тот же баннер с инфой, но без кнопки «Записаться»
        when = local(ad.datetime).strftime("%d.%m.%Y %H:%M")
        hall_name    = ad.hall.name if ad.hall else "—"
        hall_address = getattr(ad.hall, "address", "—")
        text = (
            f"🏟 <b>Зал:</b> {hall_name}\n"
            f"📍 <b>Адрес:</b> {hall_address}\n"
            f"📅 <b>Дата/Время:</b> {when}\n\n"
            f"👥 <b>Игроки ({taken_slots}/{total_slots}):</b>\n" +
            "\n".join(f"- {s.player.first_name or '—'} ({s.role})" for s in accepted) +
            "\n\n❌ Все слоты заняты."
        )
        # используем вашу клавиатуру «Назад»:
        await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="« Назад", callback_data="search_menu")]
            ]
        ))
        return
    if accepted:
        players_list = "\n".join(
            f"- {s.player.first_name or '—'} ({s.role})"
            for s in accepted
        )
        players_block = (
            f"👥 <b>Игроки ({taken_slots}/{total_slots}):</b>\n"
            f"{players_list}\n\n"
        )
    else:
        players_block = f"👥 <b>Игроки ({taken_slots}/{total_slots}):</b> нет\n\n"

    # — локализуем дату/время
    when = local(ad.datetime).strftime("%d.%m.%Y %H:%M")

    # — информация по залу
    hall_name    = ad.hall.name if ad.hall else "—"
    hall_address = getattr(ad.hall, "address", "—")

    # — итоговый текст
    text = (
        f"🏟 <b>Зал:</b> {hall_name}\n"
        f"📍 <b>Адрес:</b> {hall_address}\n"
        f"📅 <b>Дата/Время:</b> {when}\n\n"
        f"{players_block}"
        "✍️ Нажмите «Записаться», затем отправьте свою роль."
    )

    await cb.message.edit_text(
        text,
        reply_markup=signup_kb(ad_id, ad.is_paid)
    )
    await cb.answer()


@router.callback_query(F.data.startswith("signup_"))
async def signup_clicked(cb: CallbackQuery, state: FSMContext):
    """
    Шаг 4: пользователь нажал «Записаться» — ждём роль.
    """
    ad_id = int(cb.data.split("_", 1)[1])
    await state.update_data(ad_id=ad_id)
    await cb.message.edit_text("Введите свою игровую роль (или «-»):")
    await state.set_state(SignupStates.waiting_for_role)
    await cb.answer()


@router.message(SignupStates.waiting_for_role)
async def got_role(msg: Message, state: FSMContext):
    """
    Шаг 5: сохраняем роль, создаём/обновляем заявку и уведомляем автора.
    """
    role = msg.text.strip() or "-"
    data = await state.get_data()
    ad_id = data["ad_id"]

    async with SessionLocal() as session:
        signup = await session.scalar(
            select(Signup).where(
                Signup.announcement_id == ad_id,
                Signup.player_id       == msg.from_user.id,
                Signup.status          == SignupStatus.declined,
            )
        )
        if signup:
            signup.status = SignupStatus.pending
            signup.role   = role
        else:
            signup = Signup(
                announcement_id=ad_id,
                player_id      = msg.from_user.id,
                role           = role,
            )
            session.add(signup)

        await session.commit()
        await session.refresh(signup)
        ad = await session.get(
            Announcement, ad_id,
            options=[selectinload(Announcement.hall)]
        )

    # уведомление автору
    await notify_author(msg.bot, ad, msg.from_user, role, signup.id)

    await msg.answer("✅ Запрос отправлен. Ожидайте подтверждения.")
    await state.clear()
