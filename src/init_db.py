from src.models.base import Base, engine

def init_db():
    # УДАЛЯЕМ старые таблицы
    Base.metadata.drop_all(bind=engine)
    # СОЗДАЁМ заново все таблицы по моделям
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized (dropped & recreated)")

if __name__ == "__main__":
    init_db()
