# ==========================================================
# app/api.py — FastAPI adapter for WorkFriend WAI
# ==========================================================

from fastapi import FastAPI
from pydantic import BaseModel

from app.chatbot import handle_message

# IMPORTANT:
# Hugging Face expects the ASGI app to be named `app`
app = FastAPI(title="WorkFriend WAI API")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    reply = handle_message(req.message)
    return {"reply": reply}
