from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

class YesNoCallback(CallbackData, prefix="yn"):
    answer: str  # "yes" or "no"

class ConfirmCallback(CallbackData, prefix="confirm"):
    signup_id: int
    action: str  # "accept" or "decline"

def yes_no_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да", callback_data=YesNoCallback(answer="yes").pack())
    builder.button(text="❌ Нет", callback_data=YesNoCallback(answer="no").pack())
    builder.adjust(2)
    return builder.as_markup()

def confirm_kb(signup_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Принять",
        callback_data=ConfirmCallback(signup_id=signup_id, action="accept").pack()
    )
    builder.button(
        text="❌ Отклонить",
        callback_data=ConfirmCallback(signup_id=signup_id, action="decline").pack()
    )
    builder.adjust(2)
    return builder.as_markup()
