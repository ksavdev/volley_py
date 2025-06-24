#!/usr/bin/env python3
import asyncio

from src.models.base import Base, engine  # Ваши Base и AsyncEngine

async def init_db():
    # Подключаемся к БД и в асинхронном контексте вызываем синхронные DDL
    async with engine.begin() as conn:
        # Удаляем все таблицы
        await conn.run_sync(Base.metadata.drop_all)
        # Создаём их заново по актуальным моделям
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db())
