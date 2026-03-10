from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from backend.app.database import get_db
from backend.app.models import Insight
from backend.app.schemas import InsightResponse
from backend.app.core.auth import get_current_user

# Import the new advanced agents
from backend.app.agents.predictive_analytics import predictive_analytics_agent

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("/", response_model=List[InsightResponse])
def get_insights(
        user_id: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get comprehensive AI-generated insights.

    Includes:
    - Anomaly detection
    - Budget warnings
    - Behavioral analysis
    - Spending predictions
    - Optimization opportunities
    - Goal tracking
    """

    # Run comprehensive analysis with advanced agent
    predictive_analytics_agent.run_comprehensive_analysis(db, user_id)

    # Return all insights sorted by priority
    insights = db.query(Insight) \
        .filter(Insight.user_id == user_id) \
        .order_by(Insight.created_at.desc()) \
        .all()

    return insights


@router.post("/refresh")
def refresh_insights(
        user_id: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Manually trigger insights regeneration.
    """
    count = predictive_analytics_agent.run_comprehensive_analysis(db, user_id)

    return {
        "status": "success",
        "insights_generated": count,
        "message": f"Generated {count} new insights"
    }