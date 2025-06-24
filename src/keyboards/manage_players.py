from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Sequence

def players_kb(
    players: Sequence[tuple[int, str, str, float]],
    announcement_id: int
) -> InlineKeyboardMarkup:
    """
    players: список кортежей (player_id, name, role, rating)
    Каждая кнопка теперь запускает удаление игрока:
      callback_data = "remove_{announcement_id}_{player_id}"
    """
    rows: list[list[InlineKeyboardButton]] = []
    for player_id, name, role, rating in players:
        text = f"{name} ({role}) ⭐{rating:.2f}"
        rows.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"remove_{announcement_id}_{player_id}"
            )
        ])
    # Явная кнопка «Назад»
    rows.append([
        InlineKeyboardButton(
            text="Назад",
            callback_data=f"back:{announcement_id}"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)
