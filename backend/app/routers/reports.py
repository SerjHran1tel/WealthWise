from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Optional

from app.database import get_db
from app.agents.report_agent import report_agent
from app.core.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])


class WeeklyReportResponse(BaseModel):
    period: str
    stats: Dict
    comparison: Dict
    top_categories: List[Dict]
    issues: List[str]
    recommendations: List[str]
    goals_progress: List[Dict]


@router.get("/weekly", response_model=WeeklyReportResponse)
async def get_weekly_report(
        user_id: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Генерирует еженедельный отчёт с аналитикой и рекомендациями.

    Включает:
    - Статистику за последние 7 дней
    - Сравнение с предыдущей неделей
    - Топ категорий расходов
    - Выявленные проблемы
    - AI-generated рекомендации
    - Прогресс по целям
    """
    try:
        logger.info(f"Generating weekly report for user {user_id}")

        report = await report_agent.generate_weekly_report(db, user_id)

        return WeeklyReportResponse(**report)

    except Exception as e:
        logger.error(f"Error generating weekly report: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate report: {str(e)}"
        )


@router.post("/trigger-weekly")
async def trigger_weekly_report_for_all(db: Session = Depends(get_db)):
    """
    Триггер для генерации еженедельных отчётов для всех пользователей.
    Можно вызывать по расписанию (cron).
    """
    # В реальном приложении здесь был бы список всех пользователей
    # Для MVP используем тестового пользователя

    TEST_USER_ID = "00000000-0000-0000-0000-000000000001"

    try:
        report = await report_agent.generate_weekly_report(db, TEST_USER_ID)

        return {
            "status": "success",
            "message": "Weekly reports generated",
            "users_processed": 1
        }

    except Exception as e:
        logger.error(f"Error in weekly report trigger: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger reports: {str(e)}"
        )