from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Sequence
from src.models.announcement import Announcement
from src.utils.helpers import local


def ad_list_kb(ads: Sequence[Announcement]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{a.hall.name} • {local(a.datetime).strftime('%d.%m %H:%M')} • свободно {free_slots(a)}",
                callback_data=f"ad_{a.id}",
            )
        ]
        for a in ads
    ]
    rows.append([InlineKeyboardButton(text="« Назад", callback_data="search_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def free_slots(a: Announcement) -> int:
    accepted = sum(1 for s in a.signups if s.status.name == "accepted")
    return max(a.players_need - accepted, 0)
