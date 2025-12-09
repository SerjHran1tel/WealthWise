from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Insight
from app.schemas import InsightResponse
from app.agents.analytics import analytics_agent
from app.agents.forecaster import forecast_agent  # <-- Импорт

router = APIRouter(prefix="/api/insights", tags=["insights"])

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"


@router.get("/", response_model=List[InsightResponse])
def get_insights(db: Session = Depends(get_db)):
    """Получить список актуальных инсайтов (аналитика + прогнозы)"""

    # 1. Запускаем аналитику (поиск аномалий)
    analytics_agent.run_analysis(db, TEST_USER_ID)

    # 2. Запускаем прогнозирование (будущее)
    forecast_agent.generate_forecast(db, TEST_USER_ID)

    # Возвращаем всё, сортируя по дате создания
    return db.query(Insight) \
        .filter(Insight.user_id == TEST_USER_ID) \
        .order_by(Insight.created_at.desc()) \
        .all()