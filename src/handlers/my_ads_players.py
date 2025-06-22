# src/handlers/my_ads_players.py
from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from src.models import SessionLocal
from src.models.signup import Signup, SignupStatus
from src.models.announcement import Announcement
from src.keyboards.manage_players import players_kb
from src.utils.helpers import local

router = Router(name="players")


# ────────────────────── вспомогалка ──────────────────────────
async def _render_players(message, ad: Announcement) -> None:
    """
    Обновить сообщение со списком игроков.
    Берём только заявки со статусом 'accepted'.
    """
    accepted = [su for su in ad.signups if su.status == SignupStatus.accepted]

    if not accepted:
        text = "Принятые игроки:\n\nПока нет игроков"
        # если есть кнопка «Назад» — передайте её сюда вместо None
        await message.edit_text(text, reply_markup=None)
    else:
        await message.edit_text(
            f"Принятые игроки ({ad.hall.name} "
            f"{local(ad.datetime).strftime('%d.%m %H:%M')}):",
            reply_markup=players_kb(accepted, ad.id),
        )


# ────────── «Игроки» в меню /my (author) ─────────────────────
@router.callback_query(F.data.startswith("players_"))
async def show_players(cb: CallbackQuery):
    ad_id = int(cb.data.split("_")[1])

    async with SessionLocal() as session:
        ad = await session.get(
            Announcement,
            ad_id,
            options=[
                selectinload(Announcement.hall),
                selectinload(Announcement.signups)
                .selectinload(Signup.player),
            ],
        )

    if not ad:
        await cb.answer("Объявление не найдено.", show_alert=True)
        return

    await _render_players(cb.message, ad)
    await cb.answer()


# ────────── автор удаляет игрока до игры ──────────────────────
@router.callback_query(F.data.startswith("kick_"))
async def kick_player(cb: CallbackQuery):
    ad_id, player_id = map(int, cb.data.split("_")[1:])

    async with SessionLocal() as session:
        signup = await session.scalar(
            select(Signup)
            .where(
                Signup.announcement_id == ad_id,
                Signup.player_id == player_id,
                Signup.status == SignupStatus.accepted,
            )
        )
        if not signup:
            await cb.answer("Игрок уже убран.", show_alert=True)
            return

        signup.status = SignupStatus.declined
        await session.commit()

        # Обновляем объявление, чтобы в _render_players были актуальные данные
        await session.refresh(signup.announcement)
        ad = signup.announcement

    # Уведомляем игрока
    await cb.bot.send_message(
        player_id,
        "⛔️ Автор отменил вашу запись на тренировку."
    )

    # Перерисовываем список на месте
    await _render_players(cb.message, ad)
    await cb.answer("Игрок удалён ✅")
