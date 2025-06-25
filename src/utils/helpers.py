"""
Вспомогательные функции, не завязанные на БД или FSM.
"""

import datetime as dt
from src.utils.validators import MINSK_TZ


def now_minsk() -> dt.datetime:
    """
    Получить текущее время в часовом поясе Europe/Minsk (UTC+3).
    """
    return dt.datetime.now(MINSK_TZ)


def bold(text: str) -> str:
    return f"<b>{text}</b>"

def italic(text: str) -> str:
    return f"<i>{text}</i>"
