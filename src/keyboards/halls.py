from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Sequence
from src.models.hall import Hall


def halls_keyboard(halls: Sequence[Hall]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=h.name,
                callback_data=f"hall_{h.id}"
            )
        ]
        for h in halls
    ]

    # ↓ здесь тоже только именованные параметры!
    rows.append(
        [
            InlineKeyboardButton(
                text="➕ Сообщить администратору, что зала нет",
                callback_data="hall_request_admin"
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)
