import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, String, Float, DateTime, ForeignKey, Text, Date, JSON, Enum
from sqlalchemy.orm import relationship
from backend.app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Category(Base):
    __tablename__ = "categories"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, unique=True, index=True)
    type = Column(String, default="expense")
    icon = Column(String, nullable=True)
    keywords = Column(JSON, nullable=True)

    transactions = relationship("Transaction", back_populates="category")
    budgets = relationship("Budget", back_populates="category")


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, index=True)
    date = Column(DateTime, index=True)
    description = Column(String)
    amount = Column(Float)
    currency = Column(String, default="RUB")
    category_id = Column(String, ForeignKey("categories.id"), nullable=True)
    is_income = Column(Boolean, default=False)
    source_file = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category", back_populates="transactions")


class Budget(Base):
    __tablename__ = "budgets"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, index=True)
    category_id = Column(String, ForeignKey("categories.id"))
    amount = Column(Float)
    period = Column(String, default="month")

    category = relationship("Category", back_populates="budgets")


class Insight(Base):
    __tablename__ = "insights"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, index=True)
    type = Column(String)
    title = Column(String)
    description = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# --- НОВАЯ МОДЕЛЬ ---
class Goal(Base):
    __tablename__ = "goals"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, index=True)
    name = Column(String)  # Название (На машину)
    target_amount = Column(Float)  # Сколько надо (1 000 000)
    current_amount = Column(Float, default=0.0)  # Сколько есть (50 000)
    deadline = Column(Date, nullable=True)  # Когда нужно накопить
    color = Column(String, default="#3B82F6")  # Цвет плашки
    created_at = Column(DateTime, default=datetime.utcnow)