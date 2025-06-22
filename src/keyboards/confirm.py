# src/keyboards/confirm.py

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def confirm_keyboard(signup_id: int) -> InlineKeyboardMarkup:
    """
    Динамические кнопки для конкретной заявки:
      ✅ Принять  → callback_data="signup:{id}:accept"
      ❌ Отклонить → callback_data="signup:{id}:decline"
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принять",
                    callback_data=f"signup:{signup_id}:accept"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"signup:{signup_id}:decline"
                )
            ]
        ]
    )
