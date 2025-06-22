# src/keyboards/manage_players.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def players_kb(players: list[tuple[int, str, float]], announcement_id: int) -> InlineKeyboardMarkup:
    # Формируем список рядов (каждый ряд - список из одной кнопки)
    keyboard_rows: list[list[InlineKeyboardButton]] = []
    for player_id, name, rating in players:
        text = f"{name} ⭐{rating}"
        callback = f"kick:{announcement_id}:{player_id}"
        keyboard_rows.append([InlineKeyboardButton(text=text, callback_data=callback)])
    # Добавляем в конце ряд с кнопкой "Назад"
    keyboard_rows.append([InlineKeyboardButton(text="Назад", callback_data=f"back:{announcement_id}")])
    # Создаем и возвращаем разметку клавиатуры
    return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)