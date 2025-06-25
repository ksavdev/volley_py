# src/handlers/my_ads.py
from __future__ import annotations

from typing import List
import re

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models import SessionLocal
from src.models.announcement import Announcement
from src.models.signup import Signup, SignupStatus
from src.keyboards.manage_players import players_kb
from src.keyboards.announce_manage import manage_keyboard, list_keyboard, choose_field_keyboard
from src.utils.helpers import local, MINSK_TZ
from aiogram.fsm.context import FSMContext
from src.states.edit_states import EditStates

router = Router(name="my_ads_players")


async def _render_players(message: Message, ad: Announcement) -> None:
    """
    Обновляет/рисует сообщение со списком принятых игроков
    для конкретного объявления.
    """
    accepted: List[Signup] = [
        su for su in ad.signups if su.status == SignupStatus.accepted
    ]

    await message.edit_text(
        (
            f"Принятые игроки "
            f"({ad.hall.name} {local(ad.datetime).strftime('%d.%m %H:%M')}):"
        ),
        reply_markup=players_kb(accepted, ad.id),
    )


@router.callback_query(F.data.startswith("players_"))
async def handle_show_players(cb: CallbackQuery):
    """
    Обработчик кнопки «👥 Игроки» из меню управления объявлением.

    callback_data: players_<ad_id>
    """
    ad_id = int(cb.data.split("_")[1])

    async with SessionLocal() as session:
        ad: Announcement | None = await session.get(
            Announcement,
            ad_id,
            options=[
                selectinload(Announcement.hall),
                selectinload(Announcement.signups)
                .selectinload(Signup.player),
            ],
        )

    if ad is None:
        await cb.answer("Объявление не найдено.", show_alert=True)
        return

    await _render_players(cb.message, ad)
    await cb.answer()


@router.callback_query(F.data.startswith("kick_"))
async def handle_kick_player(cb: CallbackQuery):
    """
    Кнопка удаления игрока из тренировки.

    callback_data: kick_<ad_id>_<player_id>
    """
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

        # отмечаем, что игрок исключён
        signup.status = SignupStatus.declined
        await session.commit()

        # обновляем объявление для повторной отрисовки
        await session.refresh(signup.announcement)
        ad: Announcement = signup.announcement

    # личное уведомление игроку
    await cb.bot.send_message(
        player_id,
        "⛔️ Автор отменил вашу запись на тренировку.",
    )

    # перерисовываем текущий список
    await _render_players(cb.message, ad)
    await cb.answer("Игрок удалён ✅")


from aiogram.filters import Command


@router.message(Command("my"))
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


@router.callback_query(lambda cb: re.fullmatch(r"myad_\d+", cb.data))
async def handle_myad_details(cb: CallbackQuery):
    ad_id = int(cb.data.split("_")[1])
    async with SessionLocal() as session:
        ad: Announcement | None = await session.get(
            Announcement,
            ad_id,
            options=[selectinload(Announcement.hall)]
        )
    if ad is None:
        await cb.answer("Объявление не найдено.", show_alert=True)
        return

    text = (
        f"<b>ID:</b> {ad.id}\n"
        f"<b>Зал:</b> {ad.hall.name}\n"
        f"<b>Дата/время:</b> {local(ad.datetime).strftime('%d.%m.%Y %H:%M')}\n"
        f"<b>Нужно игроков:</b> {ad.players_need}\n"
        f"<b>Роли:</b> {ad.roles}\n"
        f"<b>Мячи:</b> {'нужны' if ad.balls_need else 'не нужны'}\n"
        f"<b>Ограничения:</b> {ad.restrictions}\n"
        f"<b>Тип:</b> {'Платная' if ad.is_paid else 'Бесплатная'}"
    )
    await cb.message.edit_text(text, reply_markup=manage_keyboard(ad.id))
    await cb.answer()


@router.callback_query(F.data == "back")
async def handle_back_to_ads(cb: CallbackQuery):
    """
    Возврат к списку объявлений по кнопке «Назад».
    """
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


@router.callback_query(F.data.startswith("myad_edit_"))
async def handle_edit_ad(cb: CallbackQuery, state: FSMContext):
    """
    Обработчик кнопки "Изменить" — открывает меню редактирования объявления.
    """
    ad_id = int(cb.data.split("_")[2])
    await state.update_data(ad_id=ad_id)
    await cb.message.edit_text("Что изменить?", reply_markup=choose_field_keyboard(ad_id))
    await state.set_state(EditStates.choosing_field)
    await cb.answer()


@router.callback_query(F.data == "edit_cancel")
async def handle_edit_cancel(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("❌ Редактирование отменено.")
    await state.clear()
    await cb.answer()
