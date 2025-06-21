from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def signup_kb(ad_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🙋‍♂️ Записаться", callback_data=f"signup_{ad_id}")],
            [InlineKeyboardButton(text="« Назад",          callback_data="search_back")],
        ]
    )
