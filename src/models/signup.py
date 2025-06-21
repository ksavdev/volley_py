from __future__ import annotations

import datetime as dt
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as PgEnum,
    ForeignKey,
    Integer,
    String,
    Column,
)
from sqlalchemy.orm import Mapped, relationship

from src.models import Base


class SignupStatus(str, Enum):
    pending   = "pending"
    accepted  = "accepted"
    declined  = "declined"


class Signup(Base):
    __tablename__ = "signups"

    # ────── колонки ────────────────────────────────────────────────
    id:            Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    player_id:     Mapped[int] = Column(Integer,   ForeignKey("users.id", ondelete="CASCADE"))
    announcement_id: Mapped[int] = Column(
        Integer,
        ForeignKey("announcements.id", ondelete="CASCADE"),
    )
    role:          Mapped[str]  = Column(String(80), nullable=True)
    status:        Mapped[SignupStatus] = Column(
        PgEnum(SignupStatus, name="signupstatus", create_constraint=True),
        default=SignupStatus.pending,
        nullable=False,
    )
    created_at:    Mapped[dt.datetime] = Column(
        DateTime(timezone=True),
        default=dt.datetime.utcnow,
        nullable=False,
    )

    # ────── связи ──────────────────────────────────────────────────
    player:       Mapped["User"]         = relationship(back_populates="signups")
    announcement: Mapped["Announcement"] = relationship(back_populates="signups")
