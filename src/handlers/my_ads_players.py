# src/handlers/my_ads_players.py

from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models import SessionLocal
from src.models.signup import Signup, SignupStatus
from src.models.announcement import Announcement
from src.handlers.announce import render_announcement
from src.utils.helpers import local
from src.keyboards.announce_manage import announcement_manage_keyboard

router = Router(name="players")


@router.callback_query(F.data.startswith("players_"))
async def show_players(cb: CallbackQuery):
    """
    Показываем список принятых игроков:
    callback.data == "players_{announcement_id}"
    """
    _, a_id = cb.data.split("_", 1)
    ann_id = int(a_id)

    async with SessionLocal() as session:
        result = await session.execute(
            select(Announcement)
            .options(
                selectinload(Announcement.hall),
                selectinload(Announcement.signups)
                    .selectinload(Signup.player),
            )
            .where(Announcement.id == ann_id)
        )
        ann = result.scalar_one_or_none()

    if not ann:
        return await cb.answer("Объявление не найдено.", show_alert=True)

    # Собираем кортежи (player_id, имя, роль, рейтинг)
    players: list[tuple[int, str, str, float]] = []
    for su in ann.signups:
        if su.status != SignupStatus.accepted:
            continue
        role = su.role or "-"
        if su.player:
            name = su.player.first_name or su.player.username or str(su.player_id)
            rating = float(su.player.rating or 0)
        else:
            name, rating = str(su.player_id), 0.0
        players.append((su.player_id, name, role, rating))

    when = local(ann.datetime).strftime("%d.%m %H:%M")
    header = f"🏐 Игроки ({ann.hall.name} • {when}):\n\n"
    body = (
        "Нет принятых игроков."
        if not players
        else "\n".join(f"{n} ({r}) ⭐{rt:.2f}" for _, n, r, rt in players)
    )

    # Кнопки удаления по одному
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"❌ Удалить {name}",
                    callback_data=f"confirm_remove_{ann.id}_{pid}"
                )
            ]
            for pid, name, *_ in players
        ] + [
            [InlineKeyboardButton(text="« Назад", callback_data=f"back:{ann.id}")]
        ]
    )

    await cb.message.edit_text(header + body, reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data.startswith("confirm_remove_"))
async def confirm_remove(cb: CallbackQuery):
    """
    Спрашиваем «Точно удалить?» перед удалением.
    callback.data == "confirm_remove_{ann_id}_{player_id}"
    """
    # Получаем ann_id и player_id
    payload = cb.data[len("confirm_remove_"):].split("_", 1)
    ann_id, player_id = map(int, payload)

    async with SessionLocal() as session:
        # Подгружаем запрос вместе с player
        result = await session.execute(
            select(Signup)
            .options(selectinload(Signup.player))
            .where(
                Signup.announcement_id == ann_id,
                Signup.player_id == player_id,
                Signup.status == SignupStatus.accepted
            )
        )
        signup = result.scalar_one_or_none()

    if not signup:
        return await cb.answer("Запись не найдена.", show_alert=True)

    role = signup.role or "-"
    if signup.player:
        name = signup.player.first_name or signup.player.username or str(player_id)
    else:
        name = str(player_id)

    text = f"Удалить игрока <b>{name}</b> (роль «{role}»)?"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="✅ Да",
                callback_data=f"do_remove_{ann_id}_{player_id}"
            ),
            InlineKeyboardButton(
                text="❌ Нет",
                callback_data=f"players_{ann_id}"
            ),
        ]]
    )
    await cb.message.edit_text(text, reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data.startswith("do_remove_"))
async def do_remove(cb: CallbackQuery):
    """
    Удаляем заявку после подтверждения.
    callback.data == "do_remove_{ann_id}_{player_id}"
    """
    payload = cb.data[len("do_remove_"):].split("_", 1)
    ann_id, player_id = map(int, payload)

    async with SessionLocal() as session:
        result = await session.execute(
            select(Signup)
            .where(
                Signup.announcement_id == ann_id,
                Signup.player_id == player_id,
                Signup.status == SignupStatus.accepted
            )
        )
        signup = result.scalar_one_or_none()
        if signup:
            await session.delete(signup)
            await session.commit()

    # Вместо перерасчёта списка игроков просто редактируем текущее сообщение
    await cb.message.edit_text("Игрок удалён, слот освобождён ✅")
    await cb.answer()


@router.callback_query(F.data.startswith("back:"))
async def back_to_announcement(cb: CallbackQuery):
    """
    Возвращаемся к карточке объявления.
    callback.data == "back:{ann_id}"
    """
    _, a_id = cb.data.split(":", 1)
    ann_id = int(a_id)

    async with SessionLocal() as session:
        result = await session.execute(
            select(Announcement)
            .options(selectinload(Announcement.hall))
            .where(Announcement.id == ann_id)
        )
        ann = result.scalar_one_or_none()

    if not ann:
        return await cb.answer("Объявление не найдено.", show_alert=True)

    text = render_announcement(ann)
    kb = announcement_manage_keyboard(ann)
    await cb.message.edit_text(text, reply_markup=kb)
    await cb.answer()
