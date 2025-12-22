from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Optional

from app.database import get_db
from app.agents.user_profiler import user_profiler
from app.core.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/profile", tags=["profile"])


class UserProfileResponse(BaseModel):
    user_id: str
    generated_at: str
    financial_behavior: Dict
    spending_patterns: Dict
    preferences: Dict
    goals_mindset: Dict
    risk_profile: Dict
    personalization_data: Dict


@router.get("/", response_model=UserProfileResponse)
def get_user_profile(
        user_id: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Получить финансовый профиль пользователя для персонализации AI.

    Профиль включает:
    - Тип финансового поведения (saver/spender/balanced)
    - Паттерны трат (временные предпочтения, импульсивность)
    - Предпочтения (бюджеты, цели)
    - Мышление о целях (долгосрочное/краткосрочное)
    - Риск-профиль (high/moderate/low)
    - Персонализированный system prompt для AI
    """
    try:
        logger.info(f"Building profile for user {user_id}")

        profile = user_profiler.build_user_profile(db, user_id)

        return UserProfileResponse(**profile)

    except Exception as e:
        logger.error(f"Error building profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build user profile: {str(e)}"
        )


@router.post("/refresh")
def refresh_user_profile(
        user_id: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Принудительно обновить профиль пользователя.

    Используется когда:
    - Добавлено много новых транзакций
    - Изменились цели или бюджеты
    - Пользователь хочет пересчитать персонализацию
    """
    try:
        profile = user_profiler.build_user_profile(db, user_id)

        return {
            "status": "success",
            "message": "Profile refreshed",
            "profile_type": profile['financial_behavior']['profile_type'],
            "data_points": profile['financial_behavior']['data_points']
        }

    except Exception as e:
        logger.error(f"Error refreshing profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh profile: {str(e)}"
        )


@router.get("/system-prompt")
def get_personalized_system_prompt(
        user_id: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Получить персонализированный system prompt для AI.

    Это промпт, который используется AI при общении с пользователем.
    Адаптирован под финансовый профиль пользователя.
    """
    try:
        system_prompt = user_profiler.get_personalized_system_prompt(db, user_id)

        return {
            "status": "success",
            "system_prompt": system_prompt,
            "user_id": user_id
        }

    except Exception as e:
        logger.error(f"Error getting system prompt: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system prompt: {str(e)}"
        )