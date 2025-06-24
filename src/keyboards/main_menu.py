from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from src.config import ADMINS

router = Router()

def main_menu_kb(user_id: int) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="🔍 Поиск тренировки")],
        [KeyboardButton(text="📋 Мои объявления")],
        [KeyboardButton(text="📝 Мои заявки")],
    ]
    if user_id in ADMINS:
        buttons.append([KeyboardButton(text="➕ Добавить зал")])
        buttons.append([KeyboardButton(text="✉️ Написать пользователю")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

