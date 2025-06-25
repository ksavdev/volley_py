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
from src.keyboards.announce_manage import announcement_manage_keyboard
from src.handlers.start import whitelist_required
from aiogram.fsm.context import FSMContext
from src.keyboards.manage_players import ManagePlayersCD, players_kb
from src.services.rating import apply_penalty

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

    players: list[Signup] = [su for su in ann.signups if su.status == SignupStatus.accepted]
    declined_players: list[Signup] = [su for su in ann.signups if su.status == SignupStatus.declined]

    when = ann.datetime.strftime("%d.%m %H:%M")
    header = f"🏐 Игроки ({ann.hall.name} • {when}):\n\n"

    body_lines = []
    kb_rows = []

    # Принятые игроки
    if players:
        body_lines.append("✅ <b>Принятые</b>")
        for su in players:
            n = su.player.fio if su.player else str(su.player_id)
            r = su.role or "-"
            rt = float(su.player.rating or 0) if su.player else 0.0
            body_lines.append(f"{n} ({r}) ⭐{rt:.2f}")
            # Кнопка удаления через фабрику
            kb_rows.append([
                InlineKeyboardButton(
                    text=f"❌ Удалить {n}",
                    callback_data=ManagePlayersCD(signup_id=su.id, penalty=0).pack()
                ),
                InlineKeyboardButton(
                    text=f"⚠️ Удалить и -1 {n}",
                    callback_data=ManagePlayersCD(signup_id=su.id, penalty=1).pack()
                ),
            ])
    else:
        body_lines.append("Нет принятых игроков.")

    # Отклонённые игроки
    if declined_players:
        body_lines.append("\n🚫 <b>Отклонённые</b>")
        for su in declined_players:
            n = su.player.fio if su.player else str(su.player_id)
            r = su.role or "-"
            rt = float(su.player.rating or 0) if su.player else 0.0
            body_lines.append(f"{n} ({r}) ⭐{rt:.2f}")
            kb_rows.append([
                InlineKeyboardButton(
                    text=f"🔓 Разблокировать {n}",
                    callback_data=f"unblock_{ann.id}_{su.player_id}"
                )
            ])

    kb_rows.append([InlineKeyboardButton(text="« Назад", callback_data=f"back:{ann.id}")])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_rows)

    await cb.message.edit_text(header + "\n".join(body_lines), reply_markup=kb)
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

    # Сообщение в чат вместо алерта
    await cb.message.answer("Игрок теперь может снова подать заявку.")

    # Обновить список игроков
    await show_players(cb)
    await show_players(cb)
    await show_players(cb)
    await show_players(cb)


@router.callback_query(ManagePlayersCD.filter())
@whitelist_required
async def do_remove(
        cb: CallbackQuery,
        state: FSMContext,
        callback_data: ManagePlayersCD,
):
    signup_id = callback_data.signup_id
    penalty   = bool(callback_data.penalty)

    async with SessionLocal() as session:
        signup: Signup = await session.get(Signup, signup_id, with_for_update=True)
        if not signup or signup.status != SignupStatus.accepted:
            await cb.answer("Заявка уже закрыта.", show_alert=True)
            return

        signup.status = SignupStatus.declined
        await session.commit()

        # Сообщение в чат вместо алерта
        msg = "Игрок удалён, рейтинг понижен." if penalty else "Игрок удалён."
        await cb.message.answer(msg)

        if penalty:
            await apply_penalty(session, signup.player_id)

    # Обновить список игроков (только одно обновление)
    await show_players(cb)
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

    # Сообщение в чат вместо алерта
    await cb.message.answer("Игрок теперь может снова подать заявку.")

    # Обновить список игроков
    await show_players(cb)
    await show_players(cb)
    await show_players(cb)
    await show_players(cb)
