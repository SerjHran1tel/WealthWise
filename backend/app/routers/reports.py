from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Optional

from backend.app.database import get_db
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


@router.post("/actions/{action_id}/execute")
async def execute_action(
        action_id: str,
        user_id: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Выполнить конкретное действие из еженедельного отчёта.

    Примеры действий:
    - increase_budget: Увеличить бюджет категории
    - cancel_subscriptions: Отменить подписки
    - deposit_to_goal: Пополнить цель
    - set_alert: Установить уведомление
    """
    try:

        logger.info(f"Executing action {action_id} for user {user_id}")

        return {
            "status": "success",
            "action_id": action_id,
            "message": f"Action {action_id} executed",
            "note": "Implementation pending"
        }

    except Exception as e:
        logger.error(f"Error executing action: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute action: {str(e)}"
        )