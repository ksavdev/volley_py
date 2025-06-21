# Используем официальный образ Python (slim для меньшего размера)
FROM python:3.11-slim

# Обновляем pip и устанавливаем зависимости
ENV PYTHONUNBUFFERED 1
WORKDIR /app

# Установим необходимые системные пакеты (например, для компиляции asyncpg, если понадобится)
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код проекта
COPY . .

# Запускаем бота
CMD alembic upgrade head && python -m src.main
