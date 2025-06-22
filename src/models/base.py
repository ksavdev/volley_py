# src/models/base.py
from __future__ import annotations
import os

from dotenv import load_dotenv
load_dotenv()

from src.config import settings
DATABASE_URL = settings.database_url

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
