# ==========================================================
# app/api.py — FastAPI routes for WorkFriend WAI
# ==========================================================

from fastapi import APIRouter
from pydantic import BaseModel

from app.chatbot import handle_message

api = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@api.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Minimal API endpoint for external callers.

    - No UI logic
    - No Gradio dependency
    - Calls the core message handler
    """
    reply = handle_message(req.message)
    return {"reply": reply}
