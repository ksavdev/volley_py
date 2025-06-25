from __future__ import annotations   # безопасно для типизации "Signup"
from decimal import Decimal, ROUND_HALF_UP
from typing import List

from sqlalchemy import BigInteger, String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from .base import Base
from .signup import Signup  # Добавьте этот импорт для корректной типизации


class User(Base):
    __tablename__ = "users"

    # Telegram ID
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    username:   Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str]       = mapped_column(String(64), nullable=False)
    last_name:  Mapped[str | None] = mapped_column(String(64))

    fio: Mapped[str | None] = mapped_column(String(128), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # ── Счётчики рейтинга ────────────────────────────────
    rating_sum:   Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rating_votes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ── Связь с заявками ─────────────────────────────────
    signups: Mapped[List["Signup"]] = relationship(
        "Signup",
        back_populates="player",
        cascade="all, delete-orphan",
    )

    # ── Рейтинг в виде гибрид-свойства ──────────────────
    @hybrid_property
    def rating(self) -> Decimal:
        """
        Возвращает средний рейтинг с точностью до сотых.
        Если голосов ещё нет — 5.00.
        """
        if self.rating_votes == 0:
            return Decimal("5.00")
        avg = Decimal(self.rating_sum) / Decimal(self.rating_votes)
        return avg.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    is_whitelisted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
