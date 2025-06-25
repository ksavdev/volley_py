"""
Вспомогательные функции, не завязанные на БД или FSM.
"""

import datetime as dt
from src.utils.validators import MINSK_TZ


def local(dt_aware: dt.datetime) -> dt.datetime:
    """
    Перевести любой aware-datetime (обычно из БД в UTC)
    в часовой пояс Europe/Minsk (UTC+3).

    >>> local(datetime.datetime(2025, 6, 21, 16, 0, tzinfo=datetime.timezone.utc))
    datetime.datetime(2025, 6, 21, 19, 0, tzinfo=datetime.timezone(datetime.timedelta(seconds=10800)))
    """
    return dt_aware.astimezone(MINSK_TZ)


def now_minsk() -> dt.datetime:
    """
    Получить текущее время в часовом поясе Europe/Minsk (UTC+3).
    """
    return dt.datetime.now(MINSK_TZ)


def bold(text: str) -> str:
    return f"<b>{text}</b>"

def italic(text: str) -> str:
    return f"<i>{text}</i>"
