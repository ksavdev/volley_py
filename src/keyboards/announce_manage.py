from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Sequence
from src.models.announcement import Announcement


def list_keyboard(ads: Sequence[Announcement]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=(
                    f"🏐 {a.id} • {a.hall.name} • "
                    f"{a.datetime.strftime('%d.%m %H:%M')}"
                ),
                callback_data=f"myad_{a.id}",
            )
        ]
        for a in ads
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def manage_keyboard(ad_id: int) -> InlineKeyboardMarkup:
    """
    Главное меню управления объявлением (после /my → выбор объявления):
    ✏️ Изменить
    🗑️ Удалить
    « Назад
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Игроки", callback_data=f"players_{ad_id}")],
            [InlineKeyboardButton(text="✏️ Изменить", callback_data=f"myad_edit_{ad_id}")],
            [InlineKeyboardButton(text="🗑️ Удалить",   callback_data=f"myad_del_{ad_id}")],
            [InlineKeyboardButton(text="« Назад",       callback_data="back")],
        ]
    )


def expired_announcement_keyboard(ad_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="« Назад в меню", callback_data="main_menu")]
        ]
    )


def choose_field_keyboard(ad_id: int) -> InlineKeyboardMarkup:
    """
    Меню после нажатия «✏️ Изменить»:
    📅 Дата
    ⏰ Время
    🔢 Кол-во игроков     — изменить число слотов (players_need)
    🎯 Роли
    🏐 Мячи
    🚧 Ограничения
    💰 Платность
    « Назад
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 Дата",             callback_data=f"edit_field_date_{ad_id}")],
            [InlineKeyboardButton(text="⏰ Время",            callback_data=f"edit_field_time_{ad_id}")],
            [InlineKeyboardButton(text="🔢 Кол-во игроков",   callback_data=f"edit_field_players_{ad_id}")],
            [InlineKeyboardButton(text="🎯 Роли",             callback_data=f"edit_field_roles_{ad_id}")],
            [InlineKeyboardButton(text="🏐 Мячи",             callback_data=f"edit_field_balls_{ad_id}")],
            [InlineKeyboardButton(text="🚧 Ограничения",      callback_data=f"edit_field_restrict_{ad_id}")],
            [InlineKeyboardButton(text="💰 Платность",        callback_data=f"edit_field_paid_{ad_id}")],
             [InlineKeyboardButton(text="« Назад",           callback_data=f"myad_{ad_id}")],
        ]
    )


def announcement_manage_keyboard(announcement: Announcement) -> InlineKeyboardMarkup:
    """
    Используется, например, чтобы вернуться из меню «Игроки».
    """
    return choose_field_keyboard(announcement.id)



