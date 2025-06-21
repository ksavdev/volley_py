from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Sequence
from src.models.announcement import Announcement
from src.utils.helpers import local


def list_keyboard(ads: Sequence[Announcement]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=(
                    f"🏐 {a.id} • {a.hall.name} • "
                    f"{local(a.datetime).strftime('%d.%m %H:%M')}"
                ),
                callback_data=f"myad_{a.id}",
            )
        ]
        for a in ads
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def manage_keyboard(ad_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Изменить", callback_data=f"myad_edit_{ad_id}"),
                InlineKeyboardButton(text="🗑 Удалить",  callback_data=f"myad_del_{ad_id}"),
            ],
            [InlineKeyboardButton(text="« Назад", callback_data="myad_back")],
        ]
    )


def choose_field_keyboard(ad_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Дата",
                                     callback_data=f"edit_field_date_{ad_id}"),
                InlineKeyboardButton(text="⏰ Время",
                                     callback_data=f"edit_field_time_{ad_id}"),
            ],
            [
                InlineKeyboardButton(text="👥 Игроки",
                                     callback_data=f"players_{ad_id}"),
                InlineKeyboardButton(text="🎯 Роли",
                                     callback_data=f"edit_field_roles_{ad_id}"),
            ],
            [
                InlineKeyboardButton(text="🏐 Мячи",
                                     callback_data=f"edit_field_balls_{ad_id}"),
                InlineKeyboardButton(text="🚧 Огр.",
                                     callback_data=f"edit_field_restrict_{ad_id}"),
            ],
            [
                InlineKeyboardButton(text="💰 Платность",
                                     callback_data=f"edit_field_paid_{ad_id}"),
            ],
            [
                InlineKeyboardButton(text="« Отмена",
                                     callback_data="edit_cancel"),
            ],
        ]
    )