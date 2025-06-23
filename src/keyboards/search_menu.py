from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def search_menu_kb() -> InlineKeyboardMarkup:
    """
    Шаг 1: Выбор типа тренировки.
    """
    keyboard = [
        [
            InlineKeyboardButton(text="💰 Платные",    callback_data="search_paid"),
            InlineKeyboardButton(text="🎉 Бесплатные", callback_data="search_free"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
