from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Sequence
from src.models.hall import Hall


def halls_keyboard(halls: Sequence[Hall], page=0, per_page=20) -> InlineKeyboardMarkup:
    start = page * per_page
    end = start + per_page
    page_halls = halls[start:end]
    rows = [
        [
            InlineKeyboardButton(
                text=h.name,
                callback_data=f"hall_{h.id}"
            )
        ]
        for h in page_halls
    ]

    # Пагинация
    nav = []
    if page > 0:
        nav.append(
            InlineKeyboardButton(
                text="« Назад",
                callback_data=f"halls_page_{page-1}"
            )
        )
    if end < len(halls):
        nav.append(
            InlineKeyboardButton(
                text="Далее »",
                callback_data=f"halls_page_{page+1}"
            )
        )
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="Нет нужного зала", callback_data="hall_request_admin")])

    return InlineKeyboardMarkup(inline_keyboard=rows)
