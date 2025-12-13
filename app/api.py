# app/api.py

from fastapi import APIRouter
from pydantic import BaseModel

from app.chatbot import handle_message

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    return {"reply": handle_message(req.message)}
