#  src/models/user.py
from __future__ import annotations
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base


class User(Base):
    __tablename__ = "users"

    id:        Mapped[int]   = mapped_column(primary_key=True)
    first_name:Mapped[str]   = mapped_column(String(128))
    rating:    Mapped[float] = mapped_column(default=5.0)

    signups:   Mapped[list["Signup"]] = relationship(
        back_populates="player", cascade="all, delete-orphan"
    )
