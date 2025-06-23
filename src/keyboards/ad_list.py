import datetime as dt
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Sequence
from src.models.announcement import Announcement
from src.utils.helpers import local
from src.utils.validators import MINSK_TZ

def ad_list_kb(ads: Sequence[Announcement]) -> InlineKeyboardMarkup:
    """
    Шаг 2: Список объявлений + «Назад» в меню выбора типа.
    """
    rows = []
    now = dt.datetime.now(MINSK_TZ)
    for ad in ads:
        when = local(ad.datetime).strftime("%d.%m %H:%M")
        text = f"{ad.hall.name} • {when} • {'Платная' if ad.is_paid else 'Бесплатная'}"
        rows.append([InlineKeyboardButton(text=text, callback_data=f"ad_{ad.id}")])

    # Кнопка «Назад» на выбор типа
    rows.append([
        InlineKeyboardButton(text="« Назад", callback_data="search_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)
