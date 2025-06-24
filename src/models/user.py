from decimal import Decimal
from typing import List

from sqlalchemy import BigInteger, String, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class User(Base):
    __tablename__ = "users"

    # Telegram ID
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    # Юзернейм (NULL, если отсутствует)
    username: Mapped[str] = mapped_column(
        String(64),
        nullable=True,
    )

    # Имя из Telegram (обязательное)
    first_name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    # Фамилия из Telegram (NULL, если не указана)
    last_name: Mapped[str] = mapped_column(
        String(64),
        nullable=True,
    )

    # ── Счётчики для расчёта рейтинга ─────────────────────────
    rating_sum: Mapped[int] = mapped_column(
        Integer,
        server_default="0",
        default=0,
        nullable=False,
    )
    rating_votes: Mapped[int] = mapped_column(
        Integer,
        server_default="0",
        default=0,
        nullable=False,
    )

    # Итоговый рейтинг (или стартовое значение)
    rating: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        server_default="5.00",
        default=Decimal("5.00"),
        nullable=False,
    )

    # ── Связь с заявками на участие в тренировках ──────────────
    signups: Mapped[List["Signup"]] = relationship(
        "Signup",
        back_populates="player",
        cascade="all, delete-orphan",
    )

    @property
    def rating_display(self) -> Decimal:
        """
        Отображаем:
        - 5.00, если ещё нет ни одного голоса;
        - иначе среднее значение с двумя знаками.
        """
        if self.rating_votes == 0:
            return Decimal("5.00")
        return (Decimal(self.rating_sum) / self.rating_votes).quantize(Decimal("0.01"))
