from aiogram import Bot
from aiogram.types import User as TgUser
from sqlalchemy import select

from src.models import SessionLocal
from src.models.user import User        # ORM-модель
from src.models.announcement import Announcement
from src.keyboards.confirm_yes_no import confirm_kb
from src.utils.helpers import local


async def notify_author(
    bot: Bot,
    ad: Announcement,
    player: TgUser,
    role: str,
    signup_id: int,
) -> None:
    """
    Шлёт автору объявления карточку с заявкой + кнопки ✅/❌.
    Включает рейтинг игрока.
    """
    # ── достаём рейтинг из БД ─────────────────────────────────
    async with SessionLocal() as session:
        db_user = await session.get(User, player.id)
        rating  = f"{db_user.rating:.2f}" if db_user else "—"

    text = (
        f"📥 <b>Новая заявка</b>\n\n"
        f"{ad.hall.name} • {local(ad.datetime).strftime('%d.%m %H:%M')}\n"
        f"Игрок: <a href='tg://user?id={player.id}'>{player.first_name}</a> "
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
        # Логируем, если автор заблокировал бота и т. д.
        print(f"[notify_author] send_message error: {e!r}")
