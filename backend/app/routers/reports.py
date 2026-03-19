from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

from backend.app.database import get_db
from backend.app.models import Budget, Goal, Transaction, Category, Insight
from backend.app.agents.weekly_report_agent import weekly_report_agent
from backend.app.services.scheduler import trigger_weekly_report_now, get_scheduler_status
from backend.app.core.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])


class ActionItem(BaseModel):
    id: str
    type: str
    priority: str
    title: str
    description: str
    actions: List[Dict]


class WeeklyReportResponse(BaseModel):
    period: str
    stats: Dict
    comparison: Dict
    top_categories: List[Dict]
    issues: List[Dict]
    recommendations: List[str]
    actions: List[Dict]
    goals_progress: List[Dict]
    generated_at: str


class SchedulerStatusResponse(BaseModel):
    running: bool
    jobs_count: int
    jobs: List[Dict]


@router.get("/weekly", response_model=WeeklyReportResponse)
async def get_weekly_report(
        user_id: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Получить еженедельный отчёт с аналитикой, рекомендациями и действиями.

    Включает:
    - Статистику за последние 7 дней
    - Сравнение с предыдущей неделей
    - Топ категорий расходов
    - Выявленные проблемы
    - AI-generated персонализированные рекомендации
    - Конкретные действия для выполнения
    - Прогресс по целям
    """
    try:
        logger.info(f"Generating weekly report for user {user_id}")

        report = await weekly_report_agent.generate_weekly_report(db, user_id)

        return WeeklyReportResponse(**report)

    except Exception as e:
        logger.error(f"Error generating weekly report: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate report: {str(e)}"
        )


@router.post("/weekly/refresh")
async def refresh_weekly_report(
        user_id: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Принудительно пересчитать отчёт, сбросив кэш."""
    try:
        report = await weekly_report_agent.generate_weekly_report(db, user_id, force=True)
        return WeeklyReportResponse(**report)
    except Exception as e:
        logger.error(f"Error refreshing weekly report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to refresh report: {str(e)}")


@router.post("/weekly/trigger")
async def trigger_weekly_report(
        user_id: str = Depends(get_current_user)
):
    """
    Вручную запустить генерацию еженедельного отчёта.

    Используется для:
    - Тестирования системы
    - Получения отчёта вне расписания
    - Повторной генерации отчёта
    """
    try:
        logger.info(f"Manual trigger: Generating weekly report for user {user_id}")

        # Запускаем генерацию отчёта
        trigger_weekly_report_now()

        return {
            "status": "success",
            "message": "Weekly report generation triggered",
            "user_id": user_id
        }

    except Exception as e:
        logger.error(f"Error triggering weekly report: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger report: {str(e)}"
        )


@router.get("/scheduler/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status_endpoint():
    """
    Получить статус scheduler и список запланированных задач.

    Показывает:
    - Запущен ли scheduler
    - Количество активных задач
    - Расписание каждой задачи
    - Время следующего запуска
    """
    try:
        status = get_scheduler_status()
        return SchedulerStatusResponse(**status)

    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get scheduler status: {str(e)}"
        )


class ActionExecuteRequest(BaseModel):
    """Параметры для выполнения действия"""
    action: str  # Тип действия: increase_budget, analyze_category, deposit_to_goal, etc.
    amount: Optional[float] = None  # Сумма (для бюджетов/целей)
    category_id: Optional[str] = None  # ID категории
    goal_id: Optional[str] = None  # ID цели


@router.post("/actions/{action_id}/execute")
async def execute_action(
        action_id: str,
        request: ActionExecuteRequest = ActionExecuteRequest(action="default"),
        user_id: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Выполнить конкретное действие из еженедельного отчёта.

    Поддерживаемые действия:
    - increase_budget: Увеличить бюджет категории на 20%
    - create_budget: Создать бюджет для категории
    - analyze_category: Получить детальный анализ категории
    - deposit_to_goal: Пополнить цель
    - set_limit_1500 / set_limit_2000: Установить дневной лимит (создать инсайт-напоминание)
    - cancel_subscriptions: Пометить подписки для аудита
    """
    try:
        logger.info(f"Executing action '{request.action}' (id={action_id}) for user {user_id}")

        # --- УВЕЛИЧИТЬ БЮДЖЕТ НА 20% ---
        if request.action == "increase_budget" and request.category_id:
            budget = db.query(Budget).filter(
                Budget.user_id == user_id,
                Budget.category_id == request.category_id
            ).first()
            if not budget:
                raise HTTPException(status_code=404, detail="Budget not found for this category")

            old_amount = budget.amount
            budget.amount = round(budget.amount * 1.2, 2)
            db.commit()

            return {
                "status": "success",
                "action_id": action_id,
                "message": f"Бюджет увеличен: {old_amount:.0f}₽ → {budget.amount:.0f}₽ (+20%)",
                "data": {"old_amount": old_amount, "new_amount": budget.amount}
            }

        # --- СОЗДАТЬ БЮДЖЕТ ---
        elif request.action == "create_budget" and request.category_id and request.amount:
            existing = db.query(Budget).filter(
                Budget.user_id == user_id,
                Budget.category_id == request.category_id
            ).first()

            if existing:
                existing.amount = request.amount
                db.commit()
                return {
                    "status": "success",
                    "action_id": action_id,
                    "message": f"Бюджет обновлён: {request.amount:.0f}₽/мес"
                }

            new_budget = Budget(
                user_id=user_id,
                category_id=request.category_id,
                amount=request.amount
            )
            db.add(new_budget)
            db.commit()

            return {
                "status": "success",
                "action_id": action_id,
                "message": f"Создан бюджет: {request.amount:.0f}₽/мес"
            }

        # --- АНАЛИЗ КАТЕГОРИИ ---
        elif request.action in ("analyze_category", "view_transactions") and request.category_id:
            month_ago = datetime.now().replace(day=1, hour=0, minute=0, second=0)
            txns = db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.category_id == request.category_id,
                Transaction.is_income == False,
                Transaction.date >= month_ago
            ).order_by(Transaction.date.desc()).limit(20).all()

            category = db.query(Category).filter(Category.id == request.category_id).first()
            total = sum(float(t.amount) for t in txns)

            return {
                "status": "success",
                "action_id": action_id,
                "message": f"Анализ категории '{category.name if category else 'N/A'}': {len(txns)} операций, итого {total:.0f}₽",
                "data": {
                    "category": category.name if category else None,
                    "transactions_count": len(txns),
                    "total": total,
                    "transactions": [
                        {"date": t.date.isoformat(), "description": t.description, "amount": float(t.amount)}
                        for t in txns[:10]
                    ]
                }
            }

        # --- ПОПОЛНИТЬ ЦЕЛЬ ---
        elif request.action == "deposit_to_goal" and request.goal_id and request.amount:
            goal = db.query(Goal).filter(
                Goal.id == request.goal_id,
                Goal.user_id == user_id
            ).first()
            if not goal:
                raise HTTPException(status_code=404, detail="Goal not found")

            old_amount = goal.current_amount
            goal.current_amount = goal.current_amount + request.amount
            db.commit()

            percentage = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0

            return {
                "status": "success",
                "action_id": action_id,
                "message": f"Цель '{goal.name}' пополнена: +{request.amount:.0f}₽ (прогресс: {percentage:.1f}%)",
                "data": {
                    "old_amount": old_amount,
                    "new_amount": goal.current_amount,
                    "percentage": round(percentage, 1)
                }
            }

        # --- УСТАНОВИТЬ ДНЕВНОЙ ЛИМИТ ---
        elif request.action in ("set_limit_1500", "set_limit_2000", "custom_limit"):
            limit_map = {"set_limit_1500": 1500, "set_limit_2000": 2000, "custom_limit": request.amount or 2000}
            daily_limit = limit_map.get(request.action, 2000)

            insight = Insight(
                user_id=user_id,
                type="daily_limit",
                title=f"Дневной лимит: {daily_limit:.0f}₽",
                description=f"Вы установили дневной лимит расходов {daily_limit:.0f}₽. Старайтесь не превышать эту сумму."
            )
            db.add(insight)
            db.commit()

            return {
                "status": "success",
                "action_id": action_id,
                "message": f"Дневной лимит установлен: {daily_limit:.0f}₽",
                "data": {"daily_limit": daily_limit}
            }

        # --- АУДИТ ПОДПИСОК ---
        elif request.action in ("cancel_subscriptions", "mark_essential"):
            insight = Insight(
                user_id=user_id,
                type="subscription_audit",
                title="Аудит подписок запущен",
                description="Проверьте свои регулярные платежи и отмените ненужные подписки."
            )
            db.add(insight)
            db.commit()

            return {
                "status": "success",
                "action_id": action_id,
                "message": "Аудит подписок запущен. Проверьте раздел инсайтов."
            }

        # --- DEFAULT / SET_ALERT ---
        else:
            insight = Insight(
                user_id=user_id,
                type="action_reminder",
                title=f"Напоминание: {action_id}",
                description=f"Действие '{request.action}' зафиксировано. Мы напомним вам о нём."
            )
            db.add(insight)
            db.commit()

            return {
                "status": "success",
                "action_id": action_id,
                "message": f"Действие '{request.action}' зафиксировано как напоминание"
            }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error executing action: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute action: {str(e)}"
        )