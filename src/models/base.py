# src/models/base.py
from __future__ import annotations
import os

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, registry

DATABASE_URL = os.getenv("DATABASE_URL")  # <-- берём из .env

# ─── engine ───────────────────────────────────────────────────
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

# ─── фабрика сессий ───────────────────────────────────────────
SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# ─── Declarative Base ─────────────────────────────────────────
mapper_registry = registry()

class Base(DeclarativeBase):
    registry = mapper_registry
