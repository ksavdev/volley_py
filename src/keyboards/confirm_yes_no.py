from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def confirm_kb(signup_id: int) -> InlineKeyboardMarkup:
    """
    Динамические кнопки «Принять» / «Отклонить» для конкретной заявки.
    callback_data = "signup:{signup_id}:accept" / "signup:{signup_id}:decline"
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[[  # одна строка с двумя кнопками
            InlineKeyboardButton(
                text="✅ Принять",
                callback_data=f"signup:{signup_id}:accept"
            ),
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"signup:{signup_id}:decline"
            ),
        ]]
    )
