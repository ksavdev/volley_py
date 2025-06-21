from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def confirm_kb(signup_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять",  callback_data=f"acc_{signup_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"dec_{signup_id}"),
            ]
        ]
    )
