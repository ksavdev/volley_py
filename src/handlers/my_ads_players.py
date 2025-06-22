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
from src.utils.helpers import local

router = Router(name="players")


# ────────────────────── вспомогалка ──────────────────────────
async def _render_players(message, ad: Announcement) -> None:
    """Обновить сообщение со списком игроков."""
    # берём только подтверждённых
    accepted = [su for su in ad.signups if su.status == SignupStatus.accepted]

    await message.edit_text(
        f"Принятые игроки ({ad.hall.name} "
        f"{local(ad.datetime).strftime('%d.%m %H:%M')}):",
        reply_markup=players_kb(accepted, ad.id),
    )


# ────────── «Игроки» в меню /my (author) ─────────────────────
@router.callback_query(F.data.startswith("players_"))
async def show_players(cb: CallbackQuery):
    ad_id = int(cb.data.split("_")[1])

    async with SessionLocal() as s:
        ad = await s.get(
            Announcement,
            ad_id,
            options=[
                selectinload(Announcement.hall),
                # грузим сразу только accepted-записи + player
                selectinload(
                    Announcement.signups.and_(Signup.status == SignupStatus.accepted)
                ).selectinload(Signup.player),
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

    async with SessionLocal() as s:
        signup = await s.scalar(
            select(Signup).where(
                Signup.announcement_id == ad_id,
                Signup.player_id == player_id,
                Signup.status == SignupStatus.accepted,
            )
        )
        if not signup:
            await cb.answer("Игрок уже убран.", show_alert=True)
            return

        signup.status = SignupStatus.declined
        await s.commit()

        # обновляем объект объявления, чтобы снова передать в _render_players
        await s.refresh(signup.announcement)
        ad = signup.announcement

    # уведомляем игрока
    await cb.bot.send_message(
        player_id,
        "⛔️ Автор отменил вашу запись на тренировку.",
    )

    # перерисовываем список на месте
    await _render_players(cb.message, ad)
    await cb.answer("Игрок удалён ✅")
