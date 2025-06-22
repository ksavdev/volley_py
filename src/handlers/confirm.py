from aiogram import Router, types, exceptions
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models import SessionLocal
from src.models.signup import Signup, SignupStatus
from src.models.announcement import Announcement
from src.keyboards.confirm_yes_no import confirm_kb
from src.keyboards.announce_manage import announcement_manage_keyboard
from .announce import render_announcement
from src.utils.helpers import local

router = Router()

@router.callback_query(lambda c: c.data and c.data.startswith("signup:"))
async def confirm_signup(callback: types.CallbackQuery):
    """
    Обработка нажатий:
      callback.data == "signup:{signup_id}:accept" или "signup:{signup_id}:decline"
    1) Меняет статус заявки в базе;
    2) Рендерит у автора новое сообщение с управлением (без кнопок ✓/✗);
    3) Отправляет игроку личное сообщение о результате.
    """
    _, signup_id_str, action = callback.data.split(":")
    signup_id = int(signup_id_str)
    accepted = action == "accept"

    # ——— Работа с БД ———
    async with SessionLocal() as session:
        signup = await session.get(Signup, signup_id)
        if not signup:
            return await callback.answer("Заявка не найдена", show_alert=True)

        # 1. Обновляем статус
        signup.status = (
            SignupStatus.accepted if accepted else SignupStatus.declined
        )
        session.add(signup)
        await session.commit()

        # 2. Жадно подгружаем hall и все signups
        result = await session.execute(
            select(Announcement)
            .options(
                selectinload(Announcement.hall),
                selectinload(Announcement.signups)
            )
            .where(Announcement.id == signup.announcement_id)
        )
        announcement = result.scalar_one()

    # ——— Обновляем сообщение у автора ———
    new_text = render_announcement(announcement)
    manage_kb = announcement_manage_keyboard(announcement)
    try:
        await callback.message.edit_text(new_text, reply_markup=manage_kb)
    except exceptions.TelegramBadRequest as e:
        # Telegram ругается, если ничего не изменилось — игнорируем
        if "message is not modified" not in e.message:
            raise

    # «Гасим» индикатор (без toast-уведомления)
    await callback.answer()

    # ——— Уведомляем игрока ———
    when = local(announcement.datetime).strftime("%d.%m %H:%M")
    player_msg = (
        f"📣 Ваша заявка на тренировку в {announcement.hall.name} • {when} "
        f"{'принята' if accepted else 'отклонена'}."
    )
    try:
        await callback.bot.send_message(
            chat_id=signup.player_id,  # <— здесь обязательно player_id из модели Signup
            text=player_msg,
        )
    except Exception:
        # Игрок мог заблокировать бота — безопасно игнорируем
        pass
