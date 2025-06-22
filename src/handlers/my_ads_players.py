# src/handlers/my_ads_players.py

from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models import SessionLocal
from src.models.signup import Signup, SignupStatus
from src.models.announcement import Announcement
from src.keyboards.manage_players import players_kb
from src.keyboards.announce_manage import announcement_manage_keyboard
from src.handlers.announce import render_announcement
from src.utils.helpers import local

router = Router(name="players")


@router.callback_query(F.data.startswith("players_"))
async def show_players(cb: CallbackQuery):
    """
    Обработчик для кнопки 'Игроки'.
    callback.data == "players_{announcement_id}"
    """
    # 1) Извлекаем ID объявления
    _, a_id = cb.data.split("_", 1)
    announcement_id = int(a_id)

    # 2) Загружаем объявление вместе с hall и signups->player
    async with SessionLocal() as session:
        result = await session.execute(
            select(Announcement)
            .options(
                selectinload(Announcement.hall),
                selectinload(Announcement.signups)
                    .selectinload(Signup.player),
            )
            .where(Announcement.id == announcement_id)
        )
        announcement = result.scalar_one_or_none()

    if not announcement:
        return await cb.answer("Объявление не найдено.", show_alert=True)

    # 3) Собираем только принятых игроков
    players: list[tuple[int, str, float]] = []
    for su in announcement.signups:
        if su.status != SignupStatus.accepted:
            continue
        if su.player:
            name = su.player.first_name or su.player.username or str(su.player_id)
            rating = float(getattr(su.player, "rating", 0.0))
        else:
            # fallback — игрока нет в БД
            name = str(su.player_id)
            rating = 0.0
        players.append((su.player_id, name, rating))

    # 4) Формируем заголовок
    when = local(announcement.datetime).strftime("%d.%m %H:%M")
    header = f"🏐 Игроки ({announcement.hall.name} • {when}):\n\n"

    # 5) Формируем тело и клавиатуру
    if not players:
        body = "Нет принятых игроков."
    else:
        body = "\n".join(f"{name} ⭐{rating:.2f}" for _, name, rating in players)

    kb = players_kb(players, announcement_id)

    # 6) Редактируем сообщение
    await cb.message.edit_text(header + body, reply_markup=kb)
    await cb.answer()  # гасим индикатор


@router.callback_query(F.data.startswith("back:"))
async def back_to_announcement(cb: CallbackQuery):
    """
    Обработчик для кнопки 'Назад'.
    callback.data == "back:{announcement_id}"
    """
    # 1) Извлекаем ID объявления
    _, a_id = cb.data.split(":", 1)
    announcement_id = int(a_id)

    # 2) Загружаем объявление вместе с hall и signups
    async with SessionLocal() as session:
        result = await session.execute(
            select(Announcement)
            .options(
                selectinload(Announcement.hall),
                selectinload(Announcement.signups)
            )
            .where(Announcement.id == announcement_id)
        )
        announcement = result.scalar_one_or_none()

    if not announcement:
        return await cb.answer("Объявление не найдено.", show_alert=True)

    # 3) Формируем текст и клавиатуру управления объявлением
    text = render_announcement(announcement)
    kb = announcement_manage_keyboard(announcement)

    # 4) Редактируем сообщение у автора
    await cb.message.edit_text(text, reply_markup=kb)
    await cb.answer()  # гасим индикатор
