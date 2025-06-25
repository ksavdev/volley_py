from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Sequence

def players_kb(
    players: Sequence,  # теперь это объекты Signup с .player
    announcement_id: int
) -> InlineKeyboardMarkup:
    """
    players: список объектов Signup (player_id, name, role, rating)
    """
    rows: list[list[InlineKeyboardButton]] = []
    for signup in players:
        player = signup.player
        name = player.fio or player.first_name or player.username or str(player.id)
        role = signup.role or "-"
        rating = float(player.rating or 0)
        text = f"{name} ({role}) ⭐{rating:.2f}"
        rows.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"remove_{announcement_id}_{player.id}"
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
