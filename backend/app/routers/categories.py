from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Category
from app.schemas import CategoryResponse

router = APIRouter(prefix="/api/categories", tags=["categories"])

@router.get("/", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """Получить список всех категорий"""
    return db.query(Category).all()