from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Sequence
from src.models.signup import Signup, SignupStatus
from src.utils.helpers import local


def list_kb(signups: Sequence[Signup]) -> InlineKeyboardMarkup:
    """
    Клавиатура со списком активных заявок игрока.
    """
    rows: list[list[InlineKeyboardButton]] = []

    for s in signups:
        ann = s.announcement
        dt  = local(ann.datetime).strftime("%d.%m %H:%M")
        hall = ann.hall.name
        text = f"{hall} • {dt} • {s.status.name}"
        rows.append(
            [InlineKeyboardButton(text=text, callback_data=f"myreq_{s.id}")]
        )

    if not rows:
        rows.append(
            [InlineKeyboardButton(text="Нет активных заявок", callback_data="noop")]
        )

    rows.append([InlineKeyboardButton(text="« Назад", callback_data="main_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_cancel_kb(signup_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚫 Отменить заявку", callback_data=f"cancel_{signup_id}")],
            [InlineKeyboardButton(text="« Назад",           callback_data="my_back")],
        ]
    )
