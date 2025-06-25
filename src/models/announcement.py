from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    BigInteger,
    Column,
)
from sqlalchemy.orm import Mapped, relationship

from src.models import Base


class Announcement(Base):
    __tablename__ = "announcements"

    # ────── колонки ────────────────────────────────────────────────
    id:            Mapped[int]    = Column(Integer, primary_key=True, autoincrement=True)
    author_id:     Mapped[int]    = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    hall_id:       Mapped[int]    = Column(Integer,    ForeignKey("halls.id", ondelete="RESTRICT"))
    datetime:      Mapped[dt.datetime] = Column(
        DateTime(timezone=False),  # <--- убираем timezone=True
        nullable=False,
    )
    capacity:      Mapped[int]    = Column(Integer, nullable=False)  # ← было players_need
    roles:         Mapped[str]    = Column(String(120), nullable=True)
    balls_need:    Mapped[bool]   = Column(Boolean, nullable=False)
    restrictions:  Mapped[str]    = Column(String(120), nullable=True)
    is_paid:       Mapped[bool]   = Column(Boolean, nullable=False)
    price:         Mapped[int | None] = Column(Integer, nullable=True)  # ← новое поле
    created_at:    Mapped[dt.datetime] = Column(
        DateTime(timezone=True),
        default=dt.datetime.now(dt.timezone.utc),
        nullable=False,
    )

    # ────── связи ──────────────────────────────────────────────────
    hall = relationship("Hall", back_populates="announcements")
    signups: Mapped[list["Signup"]] = relationship(
        "Signup",
        back_populates="announcement",
        cascade="all, delete-orphan",
    )

