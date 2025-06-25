from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# signup_id  – ID строки Signup
# penalty    – 0 (без штрафа) | 1 (со штрафом)
class ManagePlayersCD(CallbackData, prefix="mpl"):
    signup_id: int
    penalty: int


def players_kb(signup_id: int, *, penalty: bool = False):
    """
    Кнопка удаления игрока (для автора объявления).
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 Удалить" if not penalty else "⚠️ Удалить со штрафом",
                    callback_data=ManagePlayersCD(signup_id=signup_id, penalty=int(penalty)).pack(),
                )
            ]
        ]
    )
    
