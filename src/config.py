import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN       = os.getenv("BOT_TOKEN")
DB_USER         = os.getenv("POSTGRES_USER")
DB_PASSWORD     = os.getenv("POSTGRES_PASSWORD")
DB_NAME         = os.getenv("POSTGRES_DB")
DB_HOST         = os.getenv("POSTGRES_HOST", "db")
DB_PORT         = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

if not BOT_TOKEN:
    raise RuntimeError("Переменная окружения BOT_TOKEN обязательна!")
