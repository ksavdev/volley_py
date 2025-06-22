# src/handlers/search.py

import datetime as dt

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
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
from src.handlers.request_notify import notify_author

router = Router(name="search")


# ───────────── /search ─────────────────────────────────────────
@router.message(Command("search"))
async def cmd_search(msg: Message):
    """
    Шаг 1: Пользователь вводит /search — показываем меню платно/бесплатно.
    """
    await msg.answer("Выберите тип тренировки:", reply_markup=search_menu_kb)


# ───────────── Платные / Бесплатные ────────────────────────────
@router.callback_query(F.data.in_({"search_paid", "search_free"}))
async def choose_type(cb: CallbackQuery):
    """
    Шаг 2: Пользователь выбрал платную или бесплатную тренировку.
    Отображаем только будущие объявления.
    """
    is_paid = cb.data == "search_paid"
    now = dt.datetime.now(MINSK_TZ)

    async with SessionLocal() as session:
        ads = (
            await session.scalars(
                select(Announcement)
                .options(
                    selectinload(Announcement.hall),
                    selectinload(Announcement.signups),
                )
                .where(
                    Announcement.is_paid == is_paid,
                    Announcement.datetime > now,               # только будущие
                )
                .order_by(Announcement.datetime)
            )
        ).all()

    if not ads:
        await cb.answer("Пока нет объявлений такого типа.", show_alert=True)
        return

    await cb.message.edit_text(
        "Доступные тренировки:", 
        reply_markup=ad_list_kb(ads)
    )
    await cb.answer()


# ───────────── Выбрано объявление ──────────────────────────────
@router.callback_query(F.data.startswith("ad_"))
async def ad_chosen(cb: CallbackQuery, state: FSMContext):
    """
    Шаг 3: Пользователь выбрал конкретное объявление из списка.
    Проверяем, нет ли у него уже активной заявки, и предлагаем записаться.
    """
    ad_id = int(cb.data.split("_", 1)[1])
    now = dt.datetime.now(MINSK_TZ)

    # Блокируем запись на уже прошедшую тренировку
    async with SessionLocal() as session:
        ad = await session.get(Announcement, ad_id)
    if ad.datetime <= now:
        await cb.answer("К сожалению, эта тренировка уже прошла.", show_alert=True)
        return

    async with SessionLocal() as session:
        exists = await session.scalar(
            select(Signup.id).where(
                Signup.announcement_id == ad_id,
                Signup.player_id == cb.from_user.id,
                Signup.status.in_([SignupStatus.pending, SignupStatus.accepted]),
            )
        )

    if exists:
        await cb.answer(
            "У вас уже есть активная заявка на эту тренировку.",
            show_alert=True,
        )
        return

    await cb.message.edit_text(
        "Нажмите «Записаться», затем отправьте свою роль.",
        reply_markup=signup_kb(ad_id),
    )
    await cb.answer()


# ───────────── Нажата кнопка «Записаться» ──────────────────────
@router.callback_query(F.data.startswith("signup_"))
async def signup_clicked(cb: CallbackQuery, state: FSMContext):
    """
    Шаг 4: Пользователь нажал «Записаться» — ждём роль.
    """
    ad_id = int(cb.data.split("_", 1)[1])
    await state.update_data(ad_id=ad_id)
    await cb.message.edit_text("Введите свою игровую роль (или «-»):")
    await state.set_state(SignupStates.waiting_for_role)
    await cb.answer()


# ───────────── Получили роль от игрока ─────────────────────────
@router.message(SignupStates.waiting_for_role)
async def got_role(msg: Message, state: FSMContext):
    """
    Шаг 5: Пользователь ввёл роль — сохраняем заявку и уведомляем автора.
    """
    role = msg.text.strip() or "-"
    data = await state.get_data()
    ad_id = data["ad_id"]

    async with SessionLocal() as session:
        # Повторно открываем заявку, если была declined
        signup = await session.scalar(
            select(Signup).where(
                Signup.announcement_id == ad_id,
                Signup.player_id == msg.from_user.id,
                Signup.status == SignupStatus.declined,
            )
        )
        if signup:
            signup.status = SignupStatus.pending
            signup.role = role
        else:
            signup = Signup(
                announcement_id=ad_id,
                player_id=msg.from_user.id,
                role=role,
            )
            session.add(signup)

        await session.commit()
        await session.refresh(signup)

        ad = await session.get(
            Announcement,
            ad_id,
            options=[selectinload(Announcement.hall)]
        )

    # уведомляем автора
    await notify_author(msg.bot, ad, msg.from_user, role, signup.id)

    await msg.answer("Запрос отправлен автору. Ожидайте подтверждения.")
    await state.clear()
