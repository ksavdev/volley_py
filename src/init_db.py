from __future__ import annotations

import asyncio
from typing import Final

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.config import settings        # DATABASE_URL берётся из .env
from src.models import Base            # все ORM-модели (User, Signup, …)

# ───────────────────────────────────────────────────────────────
#  Настройка подключения
# ───────────────────────────────────────────────────────────────
load_dotenv()                          # подхватываем переменные окружения

DATABASE_URL: Final[str] = settings.database_url

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSession = async_sessionmaker(engine, expire_on_commit=False)   # если понадобится

# ───────────────────────────────────────────────────────────────
#  Функции
# ───────────────────────────────────────────────────────────────
async def reset_database() -> None:
    """Полностью пересоздать схему: drop → create."""
    async with engine.begin() as conn:
        # 1️⃣ Сбрасываем все таблицы, FK и зависимости
        await conn.run_sync(Base.metadata.drop_all)
        # 2️⃣ Создаём заново ORM-таблицы
        await conn.run_sync(Base.metadata.create_all)

def main() -> None:
    """CLI-точка входа: `python -m src.init_db`."""
    asyncio.run(reset_database())
    print("🚀 База пересоздана")

# ───────────────────────────────────────────────────────────────
#  Запуск как модуля
# ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
