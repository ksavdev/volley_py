# src/handlers/my_ads.py
from __future__ import annotations

import re
from datetime import datetime as dt
from typing import List, Final

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models import SessionLocal
from src.models.announcement import Announcement
from src.models.signup import Signup, SignupStatus
from src.states.announce_states import AdStates
from src.keyboards.manage_players import players_kb
from src.keyboards.announce_manage import (
    manage_keyboard,
    list_keyboard,
    choose_field_keyboard,
)
from src.utils.validators import MINSK_TZ
from src.handlers.start import whitelist_required

router: Final = Router(name="my_ads")           # (было my_ads_players → логичнее my_ads)


# --------------------------------------------------------------------------- #
#                               ВСПОМОГАТЕЛЬНОЕ                               #
# --------------------------------------------------------------------------- #
async def _render_players(message: Message, ad: Announcement) -> None:
    """Перерисовывает список принятых игроков в объявлении."""
    accepted: List[Signup] = [
        su for su in ad.signups if su.status == SignupStatus.accepted
    ]

    await message.edit_text(
        (
            f"Принятые игроки "
            f"({ad.hall.name} {ad.datetime.strftime('%d.%m %H:%M')}):"
        ),
        reply_markup=players_kb(accepted, ad.id),
    )


# --------------------------------------------------------------------------- #
#                             /my  (список объявлений)                        #
# --------------------------------------------------------------------------- #
@router.message(Command("my"))
@whitelist_required
async def cmd_my_ads(message: Message):
    author_id = message.from_user.id
    async with SessionLocal() as session:
        ads = (
            await session.scalars(
                select(Announcement)
                .options(selectinload(Announcement.hall))
                .where(Announcement.author_id == author_id)
                .order_by(Announcement.datetime.desc())
            )
        ).all()

    if not ads:
        return await message.answer("У вас пока нет объявлений.")

    await message.answer("Ваши объявления:", reply_markup=list_keyboard(ads))


# --------------------------------------------------------------------------- #
#                        выбор конкретного объявления                         #
# --------------------------------------------------------------------------- #
@router.callback_query(lambda cb: re.fullmatch(r"myad_\d+", cb.data))
@whitelist_required
async def handle_myad_details(cb: CallbackQuery):
    ad_id = int(cb.data.split("_")[1])
    async with SessionLocal() as session:
        ad: Announcement | None = await session.get(
            Announcement,
            ad_id,
            options=[selectinload(Announcement.hall)],
        )
    if ad is None:
        await cb.answer("Объявление не найдено.", show_alert=True)
        return

    now = dt.now(MINSK_TZ)
    if ad.datetime <= now:
        await cb.message.edit_text(
            "❌ Это объявление уже прошло и не может быть изменено или удалено.",
        )
        await cb.answer()
        return

    text = (
        f"<b>ID:</b> {ad.id}\n"
        f"<b>Зал:</b> {ad.hall.name}\n"
        f"<b>Дата/время:</b> {ad.datetime.strftime('%d.%m.%Y %H:%M')}\n"
        f"<b>Нужно игроков:</b> {ad.capacity}\n"
        f"<b>Роли:</b> {ad.roles}\n"
        f"<b>Мячи:</b> {'нужны' if ad.balls_need else 'не нужны'}\n"
        f"<b>Ограничения:</b> {ad.restrictions}\n"
        f"<b>Тип:</b> {'Платная' if ad.is_paid else 'Бесплатная'}"
    )
    await cb.message.edit_text(text, reply_markup=manage_keyboard(ad.id))
    await cb.answer()


# --------------------------------------------------------------------------- #
#                                «Назад» / список                             #
# --------------------------------------------------------------------------- #
@router.callback_query(F.data == "back")
@whitelist_required
async def handle_back_to_ads(cb: CallbackQuery):
    author_id = cb.from_user.id
    async with SessionLocal() as session:
        ads = (
            await session.scalars(
                select(Announcement)
                .options(selectinload(Announcement.hall))
                .where(Announcement.author_id == author_id)
                .order_by(Announcement.datetime.desc())
            )
        ).all()

    if not ads:
        await cb.message.edit_text("У вас пока нет объявлений.")
    else:
        await cb.message.edit_text("Ваши объявления:", reply_markup=list_keyboard(ads))
    await cb.answer()


# --------------------------------------------------------------------------- #
#                              УДАЛЕНИЕ ОБЪЯВЛЕНИЯ                            #
# --------------------------------------------------------------------------- #
@router.callback_query(lambda cb: re.fullmatch(r"myad_del_\d+", cb.data))
@whitelist_required
async def handle_delete_ad(cb: CallbackQuery):
    ad_id = int(cb.data.split("_")[2])
    async with SessionLocal() as session:
        ad: Announcement | None = await session.get(Announcement, ad_id)

        if ad is None:
            await cb.answer("Уже удалено.", show_alert=True)
            return

        now = dt.now(MINSK_TZ)
        if ad.datetime <= now:
            await cb.answer("Нельзя удалять прошедшие тренировки!", show_alert=True)
            return

        await session.delete(ad)
        await session.commit()

    await cb.answer("Удалено ✅", show_alert=True)

    # Обновляем список объявлений
    await handle_back_to_ads(cb)


# --------------------------------------------------------------------------- #
#                          РЕЖИМ «Изменить объявление»                        #
# --------------------------------------------------------------------------- #
@router.callback_query(F.data.startswith("myad_edit_"))
@whitelist_required
async def handle_edit_ad(cb: CallbackQuery, state: FSMContext):
    """
    Кнопка «✏️ Изменить» — показываем меню выбора поля.
    """
    ad_id = int(cb.data.split("_")[2])
    async with SessionLocal() as session:
        ad: Announcement | None = await session.get(Announcement, ad_id)
        now = dt.now(MINSK_TZ)
        if not ad:
            await cb.answer("Объявление не найдено.", show_alert=True)
            return
        if ad.datetime <= now:
            await cb.answer("Нельзя изменять прошедшие тренировки!", show_alert=True)
            return

    await state.update_data(ad_id=ad_id)
    await cb.message.edit_text(
        "Что изменить?", reply_markup=choose_field_keyboard(ad_id)
    )
    await state.set_state(AdStates.choosing_field)
    await cb.answer()


# -------------   выбор конкретного поля для редактирования  --------------- #
@router.callback_query(lambda cb: re.fullmatch(r"edit_field_[a-z_]+_\d+", cb.data))
@whitelist_required
async def handle_choose_field(cb: CallbackQuery, state: FSMContext):
    _, _, field, ad_id_str = cb.data.split("_", 3)
    ad_id = int(ad_id_str)
    await state.update_data(ad_id=ad_id, field=field)

    prompts = {
        "date":            "Введите новую дату (ДД.ММ.ГГГГ):",
        "time":            "Введите новое время (ЧЧ:ММ):",
        "players":         "Сколько игроков нужно? Введите число:",
        "roles":           "Укажите роли (или «-»):",
        "balls":           "Мячи нужны? (да/нет):",
        "restrict":        "Ограничения (или «-»):",
        "paid":            "Платная тренировка? (да/нет):",
        "players_need":    "Сколько игроков нужно? Введите число:",
    }

    # если вдруг забыли обработчик
    if field not in prompts:
        return await cb.answer("Пока не реализовано.", show_alert=True)

    next_state = getattr(AdStates, f"editing_{field}", None)
    if next_state is None:
        return await cb.answer("Пока не реализовано.", show_alert=True)

    await state.set_state(next_state)
    await cb.message.answer(prompts[field])
    await cb.answer()


# --------------------------------------------------------------------------- #
#                            «Игроки» (список / kick)                         #
# --------------------------------------------------------------------------- #
@router.callback_query(F.data.startswith("players_"))
@whitelist_required
async def handle_show_players(cb: CallbackQuery):
    from src.handlers.my_ads_players import show_players
    await show_players(cb)


@router.callback_query(F.data.startswith("kick_"))
@whitelist_required
async def handle_kick_player(cb: CallbackQuery):
    ad_id, player_id = map(int, cb.data.split("_")[1:3])

    async with SessionLocal() as session:
        signup: Signup | None = await session.scalar(
            select(Signup).where(
                Signup.announcement_id == ad_id,
                Signup.player_id == player_id,
                Signup.status == SignupStatus.accepted,
            )
        )

        if signup is None:
            await cb.answer("Игрок уже удалён.", show_alert=True)
            return

        signup.status = SignupStatus.declined
        await session.commit()

        await session.refresh(signup.announcement)
        ad: Announcement = signup.announcement

    await cb.bot.send_message(
        player_id,
        "⛔️ Автор отменил вашу запись на тренировку.",
    )

    await _render_players(cb.message, ad)
    await cb.answer("Игрок удалён ✅")


# --------------------------------------------------------------------------- #
#                               «Отмена» редактирования                       #
# --------------------------------------------------------------------------- #
@router.callback_query(F.data == "edit_cancel")
@whitelist_required
async def handle_edit_cancel(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("❌ Редактирование отменено.")
    await state.clear()
    await cb.answer()
    await cb.answer()


# --------------------------------------------------------------------------- #
#                               «Отмена» редактирования                       #
# --------------------------------------------------------------------------- #
@router.callback_query(F.data == "edit_cancel")
@whitelist_required
async def handle_edit_cancel(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("❌ Редактирование отменено.")
    await state.clear()
    await cb.answer()
    await cb.answer()
