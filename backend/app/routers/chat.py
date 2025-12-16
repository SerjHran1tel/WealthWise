from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app.database import get_db
from app.agents.chat_agent import chat_agent
from app.services.ollama_client import ollama_client
from app.core.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="Сообщение пользователя")


class ChatResponse(BaseModel):
    response: str
    status: str = "success"


class HealthCheckResponse(BaseModel):
    ollama_status: str
    available_models: list[str]
    current_model: str


@router.post("/", response_model=ChatResponse)
async def chat(
        request: ChatRequest,
        user_id: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Общение с AI финансовым ассистентом.

    Ассистент может отвечать на вопросы о:
    - Балансе и текущей финансовой ситуации
    - Расходах по категориям
    - Статусе бюджетов
    - Финансовых целях
    - Последних транзакциях
    - Рекомендациях и инсайтах
    """
    try:
        logger.info(f"Processing chat message from user {user_id}: {request.message[:50]}...")

        response_text = await chat_agent.process_message(
            db=db,
            user_id=user_id,
            message=request.message
        )

        return ChatResponse(response=response_text, status="success")

    except Exception as e:
        logger.error(f"Error processing chat message: {e}", exc_info=True)
        return ChatResponse(
            response="Извините, произошла ошибка при обработке вашего запроса. Попробуйте переформулировать вопрос.",
            status="error"
        )


@router.get("/health", response_model=HealthCheckResponse)
async def check_health():
    """
    Проверяет доступность Ollama и список доступных моделей.
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
            current_model=ollama_client.model
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
            "model": ollama_client.model
        }

    except Exception as e:
        logger.error(f"Test error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error testing Ollama: {str(e)}"
        )