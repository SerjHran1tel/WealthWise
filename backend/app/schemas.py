from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List


class CategoryBase(BaseModel):
    name: str
    type: str
    icon: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: str

    model_config = ConfigDict(from_attributes=True)


class TransactionBase(BaseModel):
    date: datetime
    description: str
    amount: float
    is_income: bool
    currency: str = "RUB"


class TransactionCreate(TransactionBase):
    pass


# --- НОВАЯ СХЕМА ---
class TransactionUpdate(BaseModel):
    category_id: Optional[str] = None
    description: Optional[str] = None
    is_income: Optional[bool] = None


# -------------------

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