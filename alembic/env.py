import os
import sys
import asyncio
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

# === ДОБАВЛЕНО: гарантируем, что /app попадает в PYTHONPATH ===============
BASE_DIR = Path(__file__).resolve().parents[1]   # /app
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))
# ==========================================================================

load_dotenv()

config = context.config
fileConfig(config.config_file_name)

# --- импортируем модели, чтобы Alembic «видел» metadata -------------------
from src.models import Base            # noqa: E402,F401
import src.models.user                 # noqa: E402,F401
# при добавлении новых моделей просто импортируйте здесь их пакеты ---------

target_metadata = Base.metadata

# --- формируем URL БД из переменных окружения -----------------------------
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
config.set_main_option("sqlalchemy.url", DATABASE_URL)
# --------------------------------------------------------------------------

def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):  # sync-обёртка для async-engine
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    connectable = create_async_engine(DATABASE_URL, poolclass=NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
