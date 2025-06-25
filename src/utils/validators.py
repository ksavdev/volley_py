import re
import datetime as dt
from typing import Tuple

# Минск UTC+3
MINSK_TZ = dt.timezone(dt.timedelta(hours=3))

def local(dt_obj):
    """Return dt_obj as aware datetime in Minsk TZ (for display)."""
    if dt_obj.tzinfo is None:
        return dt_obj.replace(tzinfo=MINSK_TZ)
    return dt_obj.astimezone(MINSK_TZ)

# ────────── Регулярки ──────────
_DATE_RE = re.compile(r"^([0-3]?\d)\.([01]?\d)\.(\d{4})$")           # 1.05.2025 или 01.05.2025
_TIME_RE = re.compile(r"^([0-1]?\d|2[0-3]):([0-5]\d)$")              # 1:22 или 01:22 или 23:59


# ────────── Парсинг даты ───────
def parse_date(date_str: str) -> dt.date:
    m = _DATE_RE.fullmatch(date_str.strip())
    if not m:
        raise ValueError("Формат даты должен быть ДД.ММ.ГГГГ")
    d, mth, y = map(int, m.groups())
    try:
        date_obj = dt.date(y, mth, d)
    except ValueError:
        raise ValueError("Неверная календарная дата")
    validate_future_date(date_obj)
    return date_obj


# ────────── Парсинг времени ────
def parse_time(time_str: str) -> dt.time:
    m = _TIME_RE.fullmatch(time_str.strip())
    if not m:
        raise ValueError("Формат времени должен быть ЧЧ:ММ")
    h, mi = map(int, m.groups())
    return dt.time(h, mi, tzinfo=MINSK_TZ)


# ────────── Проверки ───────────
def validate_future_date(date_: dt.date):
    today = dt.datetime.now(MINSK_TZ).date()
    if date_ < today:
        raise ValueError("Нельзя указывать прошедшую дату")

def future_datetime(date_: dt.date, time_: dt.time):
    # Если время без tzinfo — добавить MINSK_TZ
    if time_.tzinfo is None:
        time_ = time_.replace(tzinfo=MINSK_TZ)
    dt_full = dt.datetime.combine(date_, time_)
    if dt_full <= dt.datetime.now(MINSK_TZ):
        raise ValueError("Нельзя указывать прошедшую дату/время")

def is_positive_int(text: str) -> int:
    if not text.isdigit() or int(text) <= 0:
        raise ValueError("Введите положительное число игроков")
    return int(text)

def combine_date_time_with_tz(date_: dt.date, time_: dt.time) -> dt.datetime:
    """
    Корректно объединяет дату и время с учетом tzinfo (MINSK_TZ).
    """
    # Если time_ уже с tzinfo, strip его (иначе combine не даст tz-aware)
    time_naive = time_.replace(tzinfo=None)
    dt_full = dt.datetime.combine(date_, time_naive)
    # Присваиваем tzinfo явно
    return dt_full.replace(tzinfo=MINSK_TZ)

def to_naive_datetime(dt_: dt.datetime) -> dt.datetime:
    """
    Убирает tzinfo, чтобы сохранить "как есть" в базе.
    """
    return dt_.replace(tzinfo=None)
