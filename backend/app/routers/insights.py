from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Insight
from app.schemas import InsightResponse
from app.agents.analytics import analytics_agent

router = APIRouter(prefix="/api/insights", tags=["insights"])

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"


@router.post("/generate")
def generate_insights(db: Session = Depends(get_db)):
    """Принудительный запуск анализа"""
    count = analytics_agent.run_analysis(db, TEST_USER_ID)
    return {"status": "success", "generated": count}


@router.get("/", response_model=List[InsightResponse])
def get_insights(db: Session = Depends(get_db)):
    """Получить список актуальных инсайтов"""
    # Сначала запускаем анализ (в реальном приложении это делается фоновой задачей)
    analytics_agent.run_analysis(db, TEST_USER_ID)

    return db.query(Insight) \
        .filter(Insight.user_id == TEST_USER_ID) \
        .order_by(Insight.created_at.desc()) \
        .all()