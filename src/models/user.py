from __future__ import annotations

from decimal   import Decimal
from typing    import List

from sqlalchemy import BigInteger, String, Integer, Numeric, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class User(Base):
    __tablename__ = "users"

    # ────── данные из Telegram ────────────────────────────────
    id:         Mapped[int]  = mapped_column(BigInteger, primary_key=True)
    username:   Mapped[str | None] = mapped_column(String(64))
    full_name:  Mapped[str | None] = mapped_column(String(128))
    first_name: Mapped[str | None] = mapped_column(String)

    # ────── рейтинг ───────────────────────────────────────────
    rating_sum = Column(Integer, default=0, nullable=False)
    rating_votes = Column(Integer, default=0, nullable=False)

    # Если всё-таки хотите агрегированное поле — оставляем, но
    # даём дефолт 5.00 и делаем NOT NULL (удобно для индексов).
    rating: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        default=Decimal('5.00'),
        server_default="5.00",
        nullable=False,
    )

    @property
    def rating_display(self) -> Decimal:
        """2 знака после запятой; у новичка — 5.00"""
        if self.rating_votes == 0:
            return Decimal('5.00')
        return (Decimal(self.rating_sum) / self.rating_votes).quantize(Decimal('0.01'))

    # ────── связи ─────────────────────────────────────────────
    signups: Mapped[List["Signup"]] = relationship(
        "Signup",
        back_populates="player",
        cascade="all, delete-orphan",
    )

    # ────── удобный __repr__ (не обязательно, но помогает) ───
    def __repr__(self) -> str:            # pragma: no cover
        return f"<User {self.id} {self.username!r} ⭐{self.rating_display}>"
