from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

search_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="💸 Платные", callback_data="search_paid"),
            InlineKeyboardButton(text="🆓 Бесплатные", callback_data="search_free"),
        ]
    ]
)
