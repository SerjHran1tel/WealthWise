from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import date, datetime, time

from backend.app.database import get_db
from backend.app.models import Budget, Transaction, Category
from backend.app.schemas import BudgetCreate, BudgetResponse, BudgetStatus
from backend.app.core.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/budgets", tags=["budgets"])


@router.post("/", response_model=BudgetResponse)
def create_budget(
        budget: BudgetCreate,
        user_id: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        existing = db.query(Budget).filter(
            Budget.category_id == budget.category_id,
            Budget.user_id == user_id
        ).first()

        if existing:
            existing.amount = budget.amount
            db.commit()
            db.refresh(existing)
            return existing

        new_budget = Budget(
            user_id=user_id,
            category_id=budget.category_id,
            amount=budget.amount
        )
        db.add(new_budget)
        db.commit()
        db.refresh(new_budget)
        return new_budget
    except Exception as e:
        logger.error(f"Error creating budget: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{budget_id}")
def delete_budget(
        budget_id: str,
        user_id: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == user_id
    ).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    db.delete(budget)
    db.commit()
    return {"status": "success"}


@router.get("/status", response_model=List[BudgetStatus])
def get_budgets_status(
        start_date: date,
        end_date: date,
        user_id: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(end_date, time.max)

        budgets = db.query(Budget).filter(Budget.user_id == user_id).all()
        result = []

        for b in budgets:
            spent = db.query(func.sum(Transaction.amount)) \
                        .filter(
                Transaction.user_id == user_id,
                Transaction.category_id == b.category_id,
                Transaction.is_income == False,
                Transaction.date >= start_dt,
                Transaction.date <= end_dt
            ).scalar() or 0.0

            percentage = (spent / b.amount) * 100 if b.amount > 0 else 0

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
        logger.error(f"Error in get_budgets_status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
