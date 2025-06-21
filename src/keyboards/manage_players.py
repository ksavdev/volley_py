from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Sequence
from src.models.signup import Signup, SignupStatus
from src.utils.helpers import local


def players_kb(signups: Sequence[Signup], ad_id: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for s in signups:
        if s.status != SignupStatus.accepted:
            continue
        player = s.player
        rating = f"{player.rating:.2f}" if player else "—"
        text   = f"{player.first_name} ⭐{rating}"
        rows.append(
            [InlineKeyboardButton(text=text, callback_data=f"kick_{ad_id}_{player.id}")]
        )
    if not rows:
        rows.append([InlineKeyboardButton(text="Пока нет игроков", callback_data="noop")])
    rows.append([InlineKeyboardButton(text="« Назад", callback_data="my_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
