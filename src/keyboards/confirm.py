from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

confirm_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принять", callback_data="confirm_yes")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data="confirm_no")]
    ]
)
