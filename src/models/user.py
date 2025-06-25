from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import List

from sqlalchemy import BigInteger, String, Integer
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .signup import Signup


class User(Base):
    __tablename__ = "users"

    # ── Telegram ─────────────────────────────────────────────
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username:   Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str]        = mapped_column(String(64), nullable=False)
    last_name:  Mapped[str | None] = mapped_column(String(64))
    phone:      Mapped[str | None] = mapped_column(String(32), nullable=True)  # ← добавьте это поле

    # ── Счётчики рейтинга ────────────────────────────────────
    rating_sum:   Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rating_votes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    penalties:    Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # ← NEW

    # ── Связи ────────────────────────────────────────────────
    signups: Mapped[List["Signup"]] = relationship(
        "Signup",
        back_populates="player",
        cascade="all, delete-orphan",
    )

    # ── Гибрид-свойство рейтинга ─────────────────────────────
    @hybrid_property
    def rating(self) -> Decimal:
        """
        • 5.00, если голосов нет.
        • -1.00 за каждый штраф (penalties).
        • минимум 0.00.
        """
        base = (
            Decimal("5.00")
            if self.rating_votes == 0
            else Decimal(self.rating_sum) / Decimal(self.rating_votes)
        )

        value = (base - Decimal(self.penalties)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return max(value, Decimal("0.00"))

    @property
    def fio(self) -> str:
        """
        Возвращает ФИО пользователя (first_name + last_name) или только имя, если фамилии нет.
        """
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name
