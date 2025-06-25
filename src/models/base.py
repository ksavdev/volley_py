# src/models/base.py
from __future__ import annotations
import os

from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import registry, DeclarativeBase

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
    registry = mapper_registry
