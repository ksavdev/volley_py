# src/keyboards/manage_players.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Sequence

def players_kb(
    players: Sequence[tuple[int, str, str, float]],
    announcement_id: int
) -> InlineKeyboardMarkup:
    """
    players: список кортежей (player_id, name, role, rating)
    Каждая кнопка: "Имя (роль) ⭐рейтинг"
    """
    # 1) Формируем ряды кнопок
    rows: list[list[InlineKeyboardButton]] = []
    for player_id, name, role, rating in players:
        text = f"{name} ({role}) ⭐{rating:.2f}"
        rows.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"back:{announcement_id}"
            )
        ])
    # 2) Добавляем явный «Назад»
    rows.append([
        InlineKeyboardButton(
            text="Назад",
            callback_data=f"back:{announcement_id}"
        )
    ])
    # 3) Создаём разметку
    return InlineKeyboardMarkup(inline_keyboard=rows)
