from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List

# --- Category ---
class CategoryBase(BaseModel):
    name: str
    type: str
    icon: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: str
    model_config = ConfigDict(from_attributes=True)

# --- Transaction ---
class TransactionBase(BaseModel):
    date: datetime
    description: str
    amount: float
    is_income: bool
    currency: str = "RUB"

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    category_id: Optional[str] = None
    description: Optional[str] = None
    is_income: Optional[bool] = None

class TransactionResponse(TransactionBase):
    id: str
    category: Optional[CategoryResponse] = None
    created_at: datetime
    source_file: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class UploadResponse(BaseModel):
    status: str
    imported_count: int
    message: str

# --- НОВЫЕ СХЕМЫ БЮДЖЕТОВ ---

class BudgetCreate(BaseModel):
    category_id: str
    amount: float

class BudgetResponse(BaseModel):
    id: str
    category: CategoryResponse
    amount: float
    period: str
    model_config = ConfigDict(from_attributes=True)

class BudgetStatus(BaseModel):
    """Схема для отображения прогресса по бюджету"""
    id: str
    category_name: str
    limit_amount: float
    spent_amount: float
    percentage: float
    is_exceeded: bool