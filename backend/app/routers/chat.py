from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.agents.chat_agent import chat_agent

router = APIRouter(prefix="/api/chat", tags=["chat"])

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Эндпоинт для общения с AI ассистентом
    """
    response_text = chat_agent.process_message(db, TEST_USER_ID, request.message)
    return {"response": response_text}