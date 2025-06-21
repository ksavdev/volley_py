"""
Единая точка импорта Base и моделей.
Важно: порядок импорта не критичен, так как связи объявлены
явно (строкой) и SQLAlchemy до-конфигурирует их после импорта пакета.
"""

from sqlalchemy.orm import DeclarativeBase, registry

mapper_registry = registry()


class Base(DeclarativeBase):
    registry = mapper_registry


# ── модели ─────────────────────────────────────────────────────────
from .user         import User          # noqa: E402,F401
from .hall         import Hall          # noqa: E402,F401
from .announcement import Announcement  # noqa: E402,F401
from .signup       import Signup        # noqa: E402,F401
