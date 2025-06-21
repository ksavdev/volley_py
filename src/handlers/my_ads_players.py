from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models import SessionLocal
from src.models.signup import Signup, SignupStatus
from src.models.announcement import Announcement
from src.models.user import User
from src.keyboards.manage_players import players_kb
from src.utils.helpers import local

router = Router(name="players")


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
                selectinload(Announcement.signups)
                .selectinload(Signup.player),
            ],
        )

    if not ad:
        await cb.answer("Объявление не найдено.", show_alert=True)
        return

    await cb.message.edit_text(
        f"Принятые игроки ({ad.hall.name} "
        f"{local(ad.datetime).strftime('%d.%m %H:%M')}):",
        reply_markup=players_kb(ad.signups, ad_id),
    )
    await cb.answer()


# ────────── автор удаляет игрока до игры ──────────────────────
@router.callback_query(F.data.startswith("kick_"))
async def kick_player(cb: CallbackQuery):
    ad_id, player_id = map(int, cb.data.split("_")[1:])

    async with SessionLocal() as s:
        signup = await s.scalar(
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
        await s.commit()

    await cb.bot.send_message(
        player_id,
        "⛔️ Автор отменил вашу запись на тренировку."
    )
    await cb.answer("Игрок удалён ✅")
    await cb.message.delete()
