# src/handlers/request_notify.py

from aiogram import Bot
from aiogram.types import User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import SessionLocal
from src.models.user import User
from src.models.announcement import Announcement
from src.keyboards.common_kb import confirm_kb

async def notify_author(
    bot: Bot,
    ad: Announcement,
    player: TgUser,
    role: str,
    signup_id: int,
) -> None:
    """
    Шлёт автору карточку с новой заявкой и динамическую клавиатуру.
    """
    # ─ достаём рейтинг игрока ─────────────────────────────────
    async with SessionLocal() as session:
        db_user = await session.get(User, player.id)
        rating = f"{db_user.rating:.2f}" if db_user else "—"
        fio = db_user.fio if db_user and db_user.fio else player.first_name

    text = (
        f"📥 <b>Новая заявка</b>\n\n"
        f"{ad.hall.name} • {ad.datetime.strftime('%d.%m %H:%M')}\n"
        f"Игрок: <a href='tg://user?id={player.id}'>{fio}</a> "
        f"(⭐ {rating})\n"
        f"Роль: {role}\n\n"
        "Принять или отклонить?"
    )

    try:
        await bot.send_message(
            chat_id=ad.author_id,
            text=text,
            reply_markup=confirm_kb(signup_id),
            disable_notification=True,
        )
    except Exception as e:
        print(f"[notify_author] send_message error: {e!r}")
        print(f"[notify_author] send_message error: {e!r}")
