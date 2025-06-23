from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def signup_kb(ad_id: int, is_paid: bool) -> InlineKeyboardMarkup:
    """
    Шаг 3: Кнопка «Записаться» и «Назад» — возвращает на список объявлений данного типа.
    """
    back_callback = "search_paid" if is_paid else "search_free"
    keyboard = [
        [InlineKeyboardButton(text="✍️ Записаться", callback_data=f"signup_{ad_id}")],
        [InlineKeyboardButton(text="« Назад",      callback_data=back_callback)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
