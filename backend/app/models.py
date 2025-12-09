import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, String, Float, DateTime, ForeignKey, Text, Date, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON
from app.database import Base


# Генератор UUID для SQLite (так как там нет нативного типа UUID)
def generate_uuid():
    return str(uuid.uuid4())


class Category(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, unique=True, index=True)
    type = Column(String, default="expense")  # expense / income
    icon = Column(String, nullable=True)
    keywords = Column(JSON, nullable=True)  # Для rule-based поиска

    transactions = relationship("Transaction", back_populates="category")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, index=True)  # Хардкод для MVP
    date = Column(DateTime, index=True)
    description = Column(String)
    amount = Column(Float)
    currency = Column(String, default="RUB")
    category_id = Column(String, ForeignKey("categories.id"), nullable=True)
    is_income = Column(Boolean, default=False)
    source_file = Column(String, nullable=True)  # Откуда загружено

    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category", back_populates="transactions")


# --- ЗАГЛУШКИ ДЛЯ БУДУЩИХ ФИЧ ---

class Goal(Base):
    __tablename__ = "goals"
    id = Column(String, primary_key=True, default=generate_uuid)
    # TODO: Добавить поля name, target_amount, current_amount


class Budget(Base):
    __tablename__ = "budgets"
    id = Column(String, primary_key=True, default=generate_uuid)
    # TODO: Добавить поля limit, period


class Insight(Base):
    __tablename__ = "insights"
    id = Column(String, primary_key=True, default=generate_uuid)
    # TODO: Добавить поля title, description, type