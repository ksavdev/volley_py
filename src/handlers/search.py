# src/handlers/search.py

import datetime as dt
from src.utils.helpers import MINSK_TZ

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
from src.handlers.start import whitelist_required

router = Router(name="search")


def back_to_list_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="« Назад", callback_data="search_menu")]
        ]
    )


@router.message(Command("search"))
@whitelist_required
async def cmd_search(msg: Message):
    """Шаг 1: выбор платных/бесплатных."""
    await msg.answer("Выберите тип тренировки:", reply_markup=search_menu_kb())


@router.callback_query(F.data.in_({"search_paid", "search_free"}))
@whitelist_required
async def choose_type(cb: CallbackQuery):
    is_paid = (cb.data == "search_paid")
    now = dt.datetime.now(MINSK_TZ)

    async with SessionLocal() as session:
        ads = (
            await session.scalars(
                select(Announcement)
                .where(
                    Announcement.is_paid == is_paid,
                    Announcement.datetime > now
                )
                .options(selectinload(Announcement.hall))  # ← вот это важно!
                .order_by(Announcement.datetime)
            )
        ).all()

    if not ads:
        await cb.message.edit_text("Нет подходящих тренировок.", reply_markup=None)
        await cb.answer()
        return

    await cb.message.edit_text(
        "Доступные тренировки:",
        reply_markup=ad_list_kb(ads)
    )
    await cb.answer()


@router.callback_query(F.data == "search_menu")
@whitelist_required
async def back_to_search_menu(cb: CallbackQuery):
    """Назад – на выбор платных/бесплатных."""
    await cb.message.edit_text("Выберите тип тренировки:", reply_markup=search_menu_kb())
    await cb.answer()


@router.callback_query(F.data.startswith("ad_"))
@whitelist_required
async def ad_chosen(cb: CallbackQuery, state: FSMContext):
    """
    Шаг 3: подробности объявления + кнопки «Записаться»/«Назад».
    Отображаем зал, адрес, дату, слоты и список уже ПРИНЯТЫХ игроков.
    """
    ad_id = int(cb.data.split("_", 1)[1])
    now = dt.datetime.now(MINSK_TZ)

    # — загрузка объявления с hall и signups->player
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

        # Проверяем, есть ли у пользователя уже активная заявка
        exists = await session.scalar(
            select(Signup.id).where(
                Signup.announcement_id == ad_id,
                Signup.player_id == cb.from_user.id,
                Signup.status.in_([SignupStatus.pending, SignupStatus.accepted])
            )
        )

    if exists:
        return await cb.answer(
            "У вас уже есть активная заявка на эту тренировку.",
            show_alert=True
        )

    if ad.datetime <= now:
        return await cb.answer("К сожалению, эта тренировка уже прошла.", show_alert=True)

    # — считаем слоты и готовим блок принятых игроков
    accepted = [s for s in ad.signups if s.status == SignupStatus.accepted]
    total_slots = ad.capacity
    taken_slots = len(accepted)
    slots_info = f"{taken_slots}/{total_slots}"

    if taken_slots >= total_slots:
        players_block = f"👥 <b>Игроки ({slots_info}):</b> слоты заполнены\n\n"
    else:
        if taken_slots == 0:
            players_block = f"👥 <b>Игроки ({slots_info}):</b> нет\n\n"
        else:
            players_list = "\n".join(
                f"- {s.player.fio or s.player.first_name or s.player.username or s.player_id} ({s.role})"
                for s in accepted
            )
            players_block = (
                f"👥 <b>Игроки ({slots_info}):</b>\n"
                f"{players_list}\n\n"
            )

    # — остальная информация по залу и времени
    when = local(ad.datetime).strftime("%d.%m.%Y %H:%M")
    hall_name = ad.hall.name if ad.hall else "—"
    hall_address = getattr(ad.hall, "address", "—")

    text = (
        f"🏟 <b>Зал:</b> {hall_name}\n"
        f"📍 <b>Адрес:</b> {hall_address}\n"
        f"📅 <b>Дата/Время:</b> {when}\n\n"
        f"{players_block}"
        "✍️ Нажмите «Записаться», затем отправьте свою роль."
    )

    # --- исправленное условие ---
    if taken_slots >= total_slots:
        await cb.message.edit_text(text, reply_markup=back_to_list_kb())
    else:
        await cb.message.edit_text(text, reply_markup=signup_kb(ad_id, ad.is_paid))

    await cb.answer()


@router.callback_query(F.data.startswith("signup_"))
@whitelist_required
async def signup_clicked(cb: CallbackQuery, state: FSMContext):
    """Шаг 4: ждём ввод роли."""
    ad_id = int(cb.data.split("_", 1)[1])
    await state.update_data(ad_id=ad_id)
    await cb.message.edit_text("Введите свою игровую роль (или «-»):")
    await state.set_state(SignupStates.waiting_for_role)
    await cb.answer()


@router.message(SignupStates.waiting_for_role)
@whitelist_required
async def got_role(msg: Message, state: FSMContext):
    """
    Шаг 5: сохраняем заявку и уведомляем автора.
    """
    role = msg.text.strip() or "-"
    data = await state.get_data()
    ad_id = data["ad_id"]

    async with SessionLocal() as session:
        # финальная проверка на дубликаты
        exists = await session.scalar(
            select(Signup.id).where(
                Signup.announcement_id == ad_id,
                Signup.player_id == msg.from_user.id,
                Signup.status.in_([SignupStatus.pending, SignupStatus.accepted])
            )
        )
        if exists:
            await msg.answer("У вас уже есть активная заявка на эту тренировку.")
            await state.clear()
            return

        # ищем отклонённую заявку
        declined_signup = await session.scalar(
            select(Signup).where(
                Signup.announcement_id == ad_id,
                Signup.player_id == msg.from_user.id,
                Signup.status == SignupStatus.declined
            )
        )
        if declined_signup:
            if getattr(declined_signup, "comment", None) != "cancelled_by_user":
                await msg.answer("Ваша заявка была отклонена и вы не можете подать её повторно.")
                await state.clear()
                return
            declined_signup.status = SignupStatus.pending
            declined_signup.role = role
            declined_signup.comment = None
            await session.commit()
            await session.refresh(declined_signup)
            ad = await session.get(
                Announcement, ad_id,
                options=[selectinload(Announcement.hall)]
            )
            await notify_author(msg.bot, ad, msg.from_user, role, declined_signup.id)
            await msg.answer("✅ Запрос отправлен. Ожидайте подтверждения.")
            await state.clear()
            return

        # если не было отклонённой заявки — создаём новую
        signup = Signup(
            announcement_id=ad_id,
            player_id=msg.from_user.id,
            role=role
        )
        session.add(signup)

        await session.commit()
        await session.refresh(signup)
        ad = await session.get(
            Announcement, ad_id,
            options=[selectinload(Announcement.hall)]
        )
        # уведомляем автора
        await notify_author(msg.bot, ad, msg.from_user, role, signup.id)
        await msg.answer("✅ Запрос отправлен. Ожидайте подтверждения.")

    await state.clear()
