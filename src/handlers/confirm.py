from aiogram import Router, types, exceptions
from sqlalchemy.orm import selectinload

from src.models import SessionLocal
from src.models.signup import Signup, SignupStatus
from src.models.announcement import Announcement
from src.keyboards.common_kb import ConfirmCallback
from src.handlers.start import whitelist_required

router = Router()

@router.callback_query(ConfirmCallback.filter())
@whitelist_required
async def confirm_signup(callback: types.CallbackQuery, callback_data: ConfirmCallback):
    signup_id = callback_data.signup_id
    accepted = (callback_data.action == "accept")

    # ——— Работа с БД ———
    async with SessionLocal() as session:
        signup = await session.get(
            Signup,
            signup_id,
            options=[
                selectinload(Signup.player),
                selectinload(Signup.announcement).selectinload(Announcement.hall),
            ],
        )
        if not signup:
            return await callback.answer("Заявка не найдена", show_alert=True)

        # Обновляем статус и уменьшаем слоты, если приняли
        signup.status = SignupStatus.accepted if accepted else SignupStatus.declined

        await session.commit()

        # Получаем данные для уведомлений
        player = signup.player
        ann    = signup.announcement
        when   = ann.datetime.strftime("%d.%m %H:%M")
        hall   = ann.hall.name

    # ——— Сообщение автору ———
    first = player.first_name or player.username or str(player.id)
    if accepted:
        await callback.message.edit_text(f"Игрок {first} принят ✅")
    else:
        await callback.message.edit_text(f"Игрок {first} отклонён ❌")

    # «Гасим» индикатор
    await callback.answer()

    # ——— Уведомление игроку ———
    text = (
        f"📣 Ваша заявка на тренировку в {hall} • {when} "
        f"{'принята' if accepted else 'отклонена'}."
    )
    try:
        await callback.bot.send_message(chat_id=signup.player_id, text=text)
    except exceptions.TelegramBadRequest:
        # Игрок мог заблокировать бота — безопасно игнорируем
        pass
        pass
        pass
        pass
