from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Sequence
from src.models.signup import Signup, SignupStatus
from src.utils.helpers import local


def list_kb(signups: Sequence[Signup]) -> InlineKeyboardMarkup:
    """
    Клавиатура со списком активных (pending/accepted) заявок игрока.
    """
    rows: list[list[InlineKeyboardButton]] = []
    active_statuses = {SignupStatus.pending, SignupStatus.accepted}

    for s in signups:
        if s.status not in active_statuses:
            continue

        ann  = s.announcement
        dt   = local(ann.datetime).strftime("%d.%m %H:%M")
        hall = ann.hall.name
        text = f"{hall} • {dt} • {s.status.name}"
        rows.append([InlineKeyboardButton(text=text, callback_data=f"myreq_{s.id}")])

    if not rows:
        rows.append(
            [InlineKeyboardButton(text="Нет активных заявок", callback_data="noop")]
        )

    # Назад в главное меню
    rows.append([InlineKeyboardButton(text="« Назад", callback_data="main_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_cancel_kb(signup_id: int) -> InlineKeyboardMarkup:
    """
    Кнопки для подтверждения отмены заявки.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚫 Отменить заявку",
                    callback_data=f"cancel_{signup_id}",
                )
            ],
            [InlineKeyboardButton(text="« Назад", callback_data="my_back")],
        ]
    )
