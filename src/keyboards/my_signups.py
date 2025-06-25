from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Sequence
from src.models.signup import Signup, SignupStatus


def list_kb(signups: Sequence[Signup]) -> InlineKeyboardMarkup:
    """
    Клавиатура со списком всех заявок игрока, включая отклонённые.
    """
    from src.handlers.my_signups import status_labels  # импортируйте, если нужно

    rows: list[list[InlineKeyboardButton]] = []

    for s in signups:
        ann  = s.announcement
        dt   = ann.datetime.strftime("%d.%m %H:%M")
        hall = ann.hall.name
        status = status_labels.get(s.status, s.status.name)
        text = f"{hall} • {dt} • {status}"
        rows.append([InlineKeyboardButton(text=text, callback_data=f"myreq_{s.id}")])

    if not rows:
        rows.append(
            [InlineKeyboardButton(text="Нет заявок", callback_data="noop")]
        )

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
    
