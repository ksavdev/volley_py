from __future__ import annotations

from .base import Base, SessionLocal      # ← теперь SessionLocal есть
from .user import User
from .hall import Hall
from .announcement import Announcement
from .signup import Signup


__all__ = (
    "Base",
    "SessionLocal",
    "User",
    "Hall",
    "Announcement",
    "Signup",
)
