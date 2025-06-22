# src/handlers/confirm.py

from aiogram import Router, types
from sqlalchemy.ext.asyncio import AsyncSession

# модель заявки
from ..models.signup import Signup, SignupStatus

# шаблон текста объявления — announce.py лежит рядом с confirm.py
from src.handlers.announce import render_announcement

# клавиатура управления объявлением (кнопки «изменить», «удалить», «игроки» и т.д.)
from ..keyboards.announce_manage import announcement_manage_keyboard

router = Router()


@router.callback_query(lambda c: c.data and c.data.startswith("signup:"))
async def confirm_signup(
    callback: types.CallbackQuery,
    session: AsyncSession
):
    """
    Обработчик кнопок «Принять» / «Отклонить» заявки.
    callback.data = "signup:{signup_id}:{action}"
    """
    try:
        _, signup_id, action = callback.data.split(":")
    except ValueError:
        await callback.answer("Неверный формат данных", show_alert=True)
        return

    signup = await session.get(Signup, int(signup_id))
    if not signup:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    # меняем статус
    if action == "accept":
        signup.status = SignupStatus.accepted
        feedback = "Заявка принята ✅"
    else:
        signup.status = SignupStatus.declined
        feedback = "Заявка отклонена ❌"

    # сохраняем в БД
    session.add(signup)
    await session.commit()

    # обновляем родительское объявление, чтобы подтянуть свежие signups
    await session.refresh(signup.announcement)

    # перерисовываем сообщение у автора с актуальным текстом и кнопками
    announcement = signup.announcement
    await callback.message.edit_text(
        render_announcement(announcement),
        reply_markup=announcement_manage_keyboard(announcement)
    )

    await callback.answer(feedback)
