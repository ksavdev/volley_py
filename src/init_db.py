# src/init_db.py
from __future__ import annotations
import asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from src.models import Base                       # ваши ORM-модели

# URL берём из .env или docker-compose
from src.settings import settings                 # -> postgres://user:pass@db:5432/volley
DATABASE_URL = settings.database_url

engine = create_async_engine(DATABASE_URL, echo=True)
Session = async_sessionmaker(engine, expire_on_commit=False)

DDL_DROP_SCHEMA = """
DO $$ DECLARE
    _stmt text;
BEGIN
    -- убиваем все внешние ключи
    EXECUTE (
        SELECT string_agg('ALTER TABLE '
                          || quote_ident(schemaname)||'.'||quote_ident(tablename)
                          || ' DROP CONSTRAINT '||quote_ident(conname), '; ')
        FROM pg_constraint
        JOIN pg_class      ON conrelid = pg_class.oid
        JOIN pg_namespace  ON pg_namespace.oid = pg_class.relnamespace
        WHERE contype = 'f'
    );
    -- дропаем все таблицы
    EXECUTE (
        SELECT string_agg('DROP TABLE IF EXISTS '
                          || quote_ident(schemaname)||'.'||quote_ident(relname), ', ')
        FROM pg_class
        JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace
        WHERE relkind = 'r'
          AND pg_namespace.nspname NOT IN ('pg_catalog','information_schema')
    );
END $$;
"""

async def reset_database():
    async with engine.begin() as conn:
        # 1️⃣ убиваем всё старое
        await conn.execute(DDL_DROP_SCHEMA)
        # 2️⃣ создаём заново ORM-таблицы
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(reset_database())
    print("🚀 База пересоздана")
