from decimal import Decimal
from typing import List

from sqlalchemy import BigInteger, String, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class User(Base):
    __tablename__ = "users"

    id:            Mapped[int]    = mapped_column(BigInteger, primary_key=True)
    username:      Mapped[str]    = mapped_column(String(64), nullable=True)
    full_name:     Mapped[str]    = mapped_column(String(128), nullable=True)
    first_name:    Mapped[str]    = mapped_column(String, nullable=True)

    # ── счётчики для расчёта рейтинга ────────────────────────
    rating_sum:    Mapped[int]    = mapped_column(
                         Integer, server_default="0", default=0, nullable=False
                     )
    rating_votes:  Mapped[int]    = mapped_column(
                         Integer, server_default="0", default=0, nullable=False
                     )
    # ── итоговое поле (по желанию, можно убрать и считать на лету) ──
    rating:        Mapped[Decimal] = mapped_column(
                         Numeric(3, 2), server_default="5.00", default=Decimal("5.00"), nullable=False
                     )

    # ── связи ────────────────────────────────────────────────
    signups: Mapped[List["Signup"]] = relationship(
        "Signup",
        back_populates="player",
        cascade="all, delete-orphan",
    )

    @property
    def rating_display(self) -> Decimal:
        """
        Показываем:
        - 5.00, если ещё нет ни одного голоса;
        - иначе среднее (с двумя знаками).
        """
        if self.rating_votes == 0:
            return Decimal("5.00")
        return (Decimal(self.rating_sum) / self.rating_votes).quantize(Decimal("0.01"))
