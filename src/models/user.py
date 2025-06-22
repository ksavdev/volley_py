from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
from sqlalchemy import BigInteger, String

from .base import Base

class User(Base):
    __tablename__ = "users"

    id:         Mapped[int]   = mapped_column(BigInteger, primary_key=True)  # 👉 лучше BigInteger — как в author_id
    username:   Mapped[str]   = mapped_column(String(64), nullable=True)      # ← добавлено
    full_name:  Mapped[str]   = mapped_column(String(128), nullable=True)     # ← добавлено
    first_name: Mapped[str]   = mapped_column(String, nullable=True)
    rating:     Mapped[float] = mapped_column(default=0)

    # ────── связи ──────────────────────────────────────────────
    signups: Mapped[List["Signup"]] = relationship(
        "Signup",                     # явное имя целевой модели
        back_populates="player",      # ← отвечает поле в Signup
        cascade="all, delete-orphan",
    )
