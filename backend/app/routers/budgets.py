from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import date, datetime, time

from app.database import get_db
from app.models import Budget, Transaction, Category
from app.schemas import BudgetCreate, BudgetResponse, BudgetStatus

router = APIRouter(prefix="/api/budgets", tags=["budgets"])

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"


@router.post("/", response_model=BudgetResponse)
def create_budget(budget: BudgetCreate, db: Session = Depends(get_db)):
    try:
        existing = db.query(Budget).filter(
            Budget.category_id == budget.category_id,
            Budget.user_id == TEST_USER_ID
        ).first()

        if existing:
            existing.amount = budget.amount
            db.commit()
            db.refresh(existing)
            return existing

        new_budget = Budget(
            user_id=TEST_USER_ID,
            category_id=budget.category_id,
            amount=budget.amount
        )
        db.add(new_budget)
        db.commit()
        db.refresh(new_budget)
        return new_budget
    except Exception as e:
        print(f"Error creating budget: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{budget_id}")
def delete_budget(budget_id: str, db: Session = Depends(get_db)):
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    db.delete(budget)
    db.commit()
    return {"status": "success"}


@router.get("/status", response_model=List[BudgetStatus])
def get_budgets_status(
        start_date: date,
        end_date: date,
        db: Session = Depends(get_db)
):
    try:
        # Преобразуем даты в datetime для точного сравнения
        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(end_date, time.max)

        budgets = db.query(Budget).filter(Budget.user_id == TEST_USER_ID).all()
        result = []

        for b in budgets:
            # Считаем сумму расходов
            # Используем явный фильтр, без func.date, так как у нас уже есть datetime диапазон
            spent = db.query(func.sum(Transaction.amount)) \
                        .filter(
                Transaction.user_id == TEST_USER_ID,
                Transaction.category_id == b.category_id,
                Transaction.is_income == False,
                Transaction.date >= start_dt,
                Transaction.date <= end_dt
            ).scalar() or 0.0

            percentage = (spent / b.amount) * 100 if b.amount > 0 else 0

            # Важно: b.category - это Lazy Load. Если возникнет ошибка, мы увидим её в консоли
            cat_name = b.category.name if b.category else "Deleted Category"

            result.append({
                "id": b.id,
                "category_name": cat_name,
                "limit_amount": float(b.amount),
                "spent_amount": float(spent),
                "percentage": round(percentage, 1),
                "is_exceeded": spent > b.amount
            })

        return result

    except Exception as e:
        # ВОТ ЭТО ПОКАЖЕТ НАМ РЕАЛЬНУЮ ОШИБКУ В ТЕРМИНАЛЕ
        print(f"CRITICAL ERROR in get_budgets_status: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")