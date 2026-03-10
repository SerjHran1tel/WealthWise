from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.app.database import get_db
from backend.app.models import Goal
from backend.app.schemas import GoalCreate, GoalResponse, GoalUpdate

router = APIRouter(prefix="/api/goals", tags=["goals"])

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"


@router.get("/", response_model=List[GoalResponse])
def get_goals(db: Session = Depends(get_db)):
    goals = db.query(Goal).filter(Goal.user_id == TEST_USER_ID).all()

    # Добавляем вычисляемое поле процента
    result = []
    for g in goals:
        percentage = (g.current_amount / g.target_amount * 100) if g.target_amount > 0 else 0
        # Создаем копию объекта для ответа (или можно через Pydantic from_orm)
        g_resp = GoalResponse(
            id=g.id,
            name=g.name,
            target_amount=g.target_amount,
            current_amount=g.current_amount,
            deadline=g.deadline,
            color=g.color,
            created_at=g.created_at,
            percentage=round(percentage, 1)
        )
        result.append(g_resp)
    return result


@router.post("/", response_model=GoalResponse)
def create_goal(goal: GoalCreate, db: Session = Depends(get_db)):
    new_goal = Goal(
        user_id=TEST_USER_ID,
        name=goal.name,
        target_amount=goal.target_amount,
        current_amount=goal.current_amount,
        deadline=goal.deadline,
        color=goal.color
    )
    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)

    percentage = (new_goal.current_amount / new_goal.target_amount * 100) if new_goal.target_amount > 0 else 0
    new_goal.percentage = round(percentage, 1)

    return new_goal


@router.put("/{goal_id}/deposit", response_model=GoalResponse)
def deposit_to_goal(goal_id: str, deposit: GoalUpdate, db: Session = Depends(get_db)):
    """Обновить текущую сумму (положить деньги в копилку)"""
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    goal.current_amount = deposit.current_amount
    db.commit()
    db.refresh(goal)

    percentage = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
    goal.percentage = round(percentage, 1)

    return goal


@router.delete("/{goal_id}")
def delete_goal(goal_id: str, db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    db.delete(goal)
    db.commit()
    return {"status": "success"}