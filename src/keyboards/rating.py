from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def rating_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("1", callback_data="rate_1"),
         InlineKeyboardButton("2", callback_data="rate_2"),
         InlineKeyboardButton("3", callback_data="rate_3"),
         InlineKeyboardButton("4", callback_data="rate_4"),
         InlineKeyboardButton("5", callback_data="rate_5")]
    ])
