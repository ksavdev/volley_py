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
from src.handlers.start import whitelist_required

router = Router(name="players")


@router.callback_query(F.data.startswith("players_"))
@whitelist_required
async def show_players(cb: CallbackQuery):
    ann_id = int(cb.data.split("_")[1])

    async with SessionLocal() as session:
        ann = await session.get(
            Announcement,
            ann_id,
            options=[
                selectinload(Announcement.hall),
                selectinload(Announcement.signups).selectinload(Signup.player),
            ],
        )

    if not ann:
        await cb.answer("Объявление не найдено.", show_alert=True)
        return

    players: list[tuple[int, str, str, float]] = []
    declined_players: list[tuple[int, str, str, float]] = []
    for su in ann.signups:
        role = su.role or "-"
        if su.player:
            name = su.player.fio or su.player.first_name or su.player.username or str(su.player_id)
            rating = float(su.player.rating or 0)
        else:
            name, rating = str(su.player_id), 0.0
        if su.status == SignupStatus.accepted:
            players.append((su.player_id, name, role, rating))
        elif su.status == SignupStatus.declined:
            declined_players.append((su.player_id, name, role, rating))

    when = local(ann.datetime).strftime("%d.%m %H:%M")
    header = f"🏐 Игроки ({ann.hall.name} • {when}):\n\n"

    body_lines = []
    kb_rows = []

    # Принятые игроки
    if players:
        body_lines.append("✅ <b>Принятые</b>")
        for pid, n, r, rt in players:
            body_lines.append(f"{n} ({r}) ⭐{rt:.2f}")
            kb_rows.append([
                InlineKeyboardButton(
                    text=f"❌ Удалить {n}",
                    callback_data=f"confirm_remove_{ann.id}_{pid}"
                )
            ])
    else:
        body_lines.append("Нет принятых игроков.")

    # Отклонённые игроки
    if declined_players:
        body_lines.append("\n🚫 <b>Отклонённые</b>")
        for pid, n, r, rt in declined_players:
            body_lines.append(f"{n} ({r}) ⭐{rt:.2f}")
            kb_rows.append([
                InlineKeyboardButton(
                    text=f"🔓 Разблокировать {n}",
                    callback_data=f"unblock_{ann.id}_{pid}"
                )
            ])

    kb_rows.append([InlineKeyboardButton(text="« Назад", callback_data=f"back:{ann.id}")])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_rows)

    await cb.message.edit_text(header + "\n".join(body_lines), reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data.startswith("confirm_remove_"))
@whitelist_required
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
        name = signup.player.fio or signup.player.first_name or signup.player.username or str(player_id)
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
@whitelist_required
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
@whitelist_required
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


@router.callback_query(F.data.startswith("unblock_"))
@whitelist_required
async def unblock_declined(cb: CallbackQuery):
    """
    Снимает статус "отклонено" с заявки, чтобы игрок мог снова подать заявку.
    """
    _, ann_id, player_id = cb.data.split("_")
    ann_id = int(ann_id)
    player_id = int(player_id)

    async with SessionLocal() as session:
        signup = await session.scalar(
            select(Signup).where(
                Signup.announcement_id == ann_id,
                Signup.player_id == player_id,
                Signup.status == SignupStatus.declined,
            )
        )
        if not signup:
            await cb.answer("Заявка не найдена или уже не отклонена.", show_alert=True)
            return
        # Можно либо удалить заявку, либо сменить статус на pending (или удалить)
        await session.delete(signup)
        await session.commit()

    await cb.answer("Игрок теперь может снова подать заявку.")
    # Обновить список игроков
    await show_players(cb)
