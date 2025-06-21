# src/models/user.py
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class User(Base):
    __tablename__ = "users"

    id:        Mapped[int]     = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str]    = mapped_column(String, nullable=True)
    rating:    Mapped[float]   = mapped_column(default=0)
