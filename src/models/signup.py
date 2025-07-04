from __future__ import annotations

import datetime as dt
from enum import Enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum as PgEnum,
    ForeignKey,
    Integer,
    String,
    Column,
)
from sqlalchemy.orm import Mapped, relationship

from .base import Base
from src.states.signup_states import SignupStates


class SignupStatus(str, Enum):
    pending   = "На рассмотрении"
    accepted  = "Принята"
    declined  = "Отклонена"


class Signup(Base):
    __tablename__ = "signups"



    # ────── колонки ────────────────────────────────────────────────
    id:            Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    player_id:     Mapped[int] = Column(BigInteger,   ForeignKey("users.id", ondelete="CASCADE"))
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
        default=dt.datetime.now(dt.timezone.utc),
        nullable=False,
    )
    comment:       Mapped[str]  = Column(String, nullable=True)

    # ────── связи ──────────────────────────────────────────────────
    player:       Mapped["User"]         = relationship(back_populates="signups")
    announcement: Mapped["Announcement"] = relationship(
        "Announcement", back_populates="signups"
    )
