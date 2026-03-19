from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from backend.app.database import get_db
from backend.app.services.ollama_client import ollama_client
from backend.app.core.auth import get_current_user

# Import advanced chat agent
try:
    from backend.app.agents.advanced_chat_agent import advanced_chat_agent
    USE_ADVANCED = True
except ImportError:
    # Fallback to basic agent if advanced not available
    from backend.app.agents.chat_agent import chat_agent
    USE_ADVANCED = False

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="Сообщение пользователя")


class ChatResponse(BaseModel):
    response: str
    status: str = "success"
    agent_type: str = "advanced" if USE_ADVANCED else "basic"


class HealthCheckResponse(BaseModel):
    ollama_status: str
    available_models: list[str]
    current_model: str
    agent_type: str


@router.post("/", response_model=ChatResponse)
async def chat(
        request: ChatRequest,
        user_id: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Общение с AI финансовым психологом.

    **Advanced Agent возможности:**
    - Анализ финансового здоровья
    - Выявление поведенческих паттернов (импульсивность, стресс-траты)
    - Проактивные рекомендации
    - Эмпатичный тон с конкретными действиями
    - Прогнозирование и риск-анализ

    **Примеры вопросов:**
    - "Почему я так много трачу?"
    - "Где я могу сэкономить?"
    - "Смогу ли я накопить на отпуск?"
    - "Какие у меня импульсивные траты?"
    """
    try:
        logger.info(f"Processing chat message from user {user_id}: {request.message[:50]}...")

        if USE_ADVANCED:
            response_text = await advanced_chat_agent.process_message(
                db=db,
                user_id=user_id,
                message=request.message
            )
        else:
            response_text = await chat_agent.process_message(
                db=db,
                user_id=user_id,
                message=request.message
            )

        return ChatResponse(
            response=response_text,
            status="success",
            agent_type="advanced" if USE_ADVANCED else "basic"
        )

    except Exception as e:
        logger.error(f"Error processing chat message: {e}", exc_info=True)
        return ChatResponse(
            response="Извините, произошла ошибка при обработке вашего запроса. Попробуйте переформулировать вопрос.",
            status="error",
            agent_type="advanced" if USE_ADVANCED else "basic"
        )


@router.get("/health", response_model=HealthCheckResponse)
async def check_health():
    """
    Проверяет доступность Ollama и тип используемого агента.
    """
    try:
        is_available = await ollama_client.check_health()

        if not is_available:
            raise HTTPException(
                status_code=503,
                detail="Ollama service is not available. Make sure Ollama is running on your system."
            )

        models = await ollama_client.list_models()

        return HealthCheckResponse(
            ollama_status="available",
            available_models=models,
            current_model=ollama_client.model,
            agent_type="advanced" if USE_ADVANCED else "basic"
        )

    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Error checking Ollama status: {str(e)}"
        )


@router.post("/test")
async def test_ollama(prompt: str = "Привет! Как дела?"):
    """
    Тестовый эндпоинт для проверки работы Ollama.
    """
    try:
        response = await ollama_client.generate(
            prompt=prompt,
            temperature=0.7,
            max_tokens=100
        )

        return {
            "status": "success",
            "prompt": prompt,
            "response": response,
            "model": ollama_client.model,
            "agent_type": "advanced" if USE_ADVANCED else "basic"
        }

    except Exception as e:
        logger.error(f"Test error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error testing Ollama: {str(e)}"
        )