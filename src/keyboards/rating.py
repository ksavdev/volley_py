from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def rating_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("⭐️ 1"), KeyboardButton("⭐️ 2"), KeyboardButton("⭐️ 3")],
            [KeyboardButton("⭐️ 4"), KeyboardButton("⭐️ 5")],
            [KeyboardButton("❌ Пропустить")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
