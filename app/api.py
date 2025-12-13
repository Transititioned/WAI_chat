from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.chatbot import handle_message

router = APIRouter(tags=["chat"])

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        return {"reply": handle_message(req.message)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Assistant error") from e

@router.get("/health")
async def health():
    return {"status": "ok"}
