from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, date
from typing import Optional, List, Generic, TypeVar


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
    errors: Optional[List[str]] = None


# --- Budget ---
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
    id: str
    category_name: str
    limit_amount: float
    spent_amount: float
    percentage: float
    is_exceeded: bool


# --- Insight ---
class InsightBase(BaseModel):
    type: str
    title: str
    description: str
    is_read: bool = False


class InsightResponse(InsightBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Goals (Цели) ---
class GoalCreate(BaseModel):
    name: str
    target_amount: float
    current_amount: float = 0.0
    deadline: Optional[date] = None
    color: str = "#3B82F6"


class GoalUpdate(BaseModel):
    current_amount: float  # Для пополнения цели


class GoalResponse(GoalCreate):
    id: str
    created_at: datetime
    percentage: float  # Вычисляемое поле
    model_config = ConfigDict(from_attributes=True)


# --- Pagination (ДОБАВЛЕНО) ---
class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=500, ge=1, le=501)

    @property
    def skip(self) -> int:
        """Вычисляет offset для SQL запроса"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Возвращает лимит для SQL запроса"""
        return self.page_size


# Generic type для paginated response
T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)