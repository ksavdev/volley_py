import os
from dotenv import load_dotenv
from typing import Set

from sqlalchemy import Table, Column, String, Boolean, select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base

from src.models import Base, SessionLocal  # Добавьте этот импорт

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")  # единственный источник

# ADMINS: список id через запятую, пустая строка → пустое множество
ADMINS_ENV = os.getenv("ADMINS", "")
if ADMINS_ENV.strip():
    ADMINS: Set[int] = {int(x) for x in ADMINS_ENV.split(",") if x}
else:
    ADMINS: Set[int] = set()  # пустое множество, а не {0}

class Settings:
    @property
    def database_url(self):
        return DATABASE_URL

settings = Settings()

if not BOT_TOKEN:
    raise RuntimeError("Переменная окружения BOT_TOKEN обязательна!")
if not DATABASE_URL:
    raise RuntimeError("Переменная окружения DATABASE_URL обязательна!")

ZBT_ENABLED = True  # True = режим ЗБТ (требуется whitelist), False = открыт для всех

# Таблица для хранения глобальных настроек
class GlobalSetting(Base):
    __tablename__ = "global_settings"
    key = Column(String(64), primary_key=True)
    value = Column(String(64), nullable=False)

async def set_zbt_enabled_db(value: bool):
    async with SessionLocal() as session:
        stmt = select(GlobalSetting).where(GlobalSetting.key == "zbt_enabled")
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if row:
            row.value = "1" if value else "0"
        else:
            session.add(GlobalSetting(key="zbt_enabled", value="1" if value else "0"))
        await session.commit()

async def is_zbt_enabled_db() -> bool:
    async with SessionLocal() as session:
        stmt = select(GlobalSetting).where(GlobalSetting.key == "zbt_enabled")
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if row:
            return row.value == "1"
        return True  # По умолчанию ЗБТ включён
