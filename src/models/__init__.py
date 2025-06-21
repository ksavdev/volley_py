# src/models/__init__.py
from __future__ import annotations

# сначала вытаскиваем Base / engine / SessionLocal
from .base import Base, engine, SessionLocal  # ← ОБЯЗАТЕЛЬНО!

# далее все модели (порядок импорта не важен, связи строковые)
from .user import User
from .hall import Hall
from .announcement import Announcement
from .signup import Signup

__all__ = (
    "Base",
    "engine",
    "SessionLocal",
    "User",
    "Hall",
    "Announcement",
    "Signup",
)
