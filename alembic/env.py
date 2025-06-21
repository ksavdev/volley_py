from __future__ import annotations

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from alembic import context

from src.models.base import engine, Base        # ← импортируем готовый движок

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata


async def run_migrations_online() -> None:
    async with engine.connect() as conn:
        await conn.run_sync(do_run_migrations)


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,        # для SQLite; можно убрать для Postgres
    )
    with context.begin_transaction():
        context.run_migrations()
