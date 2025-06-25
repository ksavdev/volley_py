#!/usr/bin/env python3
import asyncio
import sys

from src.models.base import Base, engine  # Ваши Base и AsyncEngine

async def init_db(force_drop=False):
    # Подключаемся к БД и в асинхронном контексте вызываем синхронные DDL
    async with engine.begin() as conn:
        if force_drop:
            # Удаляем все таблицы
            await conn.run_sync(Base.metadata.drop_all)
        # Создаём их заново по актуальным моделям
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

if __name__ == "__main__":
    force = "--force-drop" in sys.argv
    asyncio.run(init_db(force_drop=force))
