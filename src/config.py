import os
from dotenv import load_dotenv
from typing import Set

load_dotenv()

BOT_TOKEN       = os.getenv("BOT_TOKEN")
DB_USER         = os.getenv("POSTGRES_USER")
DB_PASSWORD     = os.getenv("POSTGRES_PASSWORD")
DB_NAME         = os.getenv("POSTGRES_DB")
DB_HOST         = os.getenv("POSTGRES_HOST", "db")
DB_PORT         = os.getenv("POSTGRES_PORT", "5432")
ADMINS: Set[int] = {int(x) for x in os.getenv("ADMINS", "").split(",") if x}

class Settings:
    @property
    def database_url(self):
        return os.getenv("DATABASE_URL")

settings = Settings()

if not BOT_TOKEN:
    raise RuntimeError("Переменная окружения BOT_TOKEN обязательна!")
