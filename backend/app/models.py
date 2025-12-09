import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, String, Float, DateTime, ForeignKey, Text, Date, JSON, Enum
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Category(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, unique=True, index=True)
    type = Column(String, default="expense")  # expense / income
    icon = Column(String, nullable=True)
    keywords = Column(JSON, nullable=True)

    transactions = relationship("Transaction", back_populates="category")
    budgets = relationship("Budget", back_populates="category")  # <-- Добавили связь


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


# --- НОВАЯ МОДЕЛЬ ---
class Budget(Base):
    __tablename__ = "budgets"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, index=True)
    category_id = Column(String, ForeignKey("categories.id"))
    amount = Column(Float)  # Лимит бюджета
    period = Column(String, default="month")  # В MVP только "month"

    category = relationship("Category", back_populates="budgets")