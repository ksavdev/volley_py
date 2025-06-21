from sqlalchemy import Column, Integer, String
from src.models import Base

class Hall(Base):
    __tablename__ = "halls"

    id      = Column(Integer, primary_key=True, autoincrement=True)
    name    = Column(String(120), unique=True, nullable=False)
    address = Column(String(255), nullable=True)

    def __str__(self):
        return self.name
