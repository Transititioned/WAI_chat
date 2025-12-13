# ==========================================================
# app/api.py — FastAPI adapter for WorkFriend WAI
#
# This exposes a minimal, stable HTTP API so external
# clients (e.g. Cloudflare Worker) can call the chatbot
# without relying on Gradio internals.
#
# The API delegates directly to the core message handler
# defined in app.chatbot.handle_message().
# ==========================================================

from fastapi import FastAPI
from pydantic import BaseModel

from app.chatbot import handle_message

api = FastAPI(title="WorkFriend WAI API")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@api.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Accepts a user message and returns the assistant reply.

    This endpoint is intentionally thin:
    - no UI logic
    - no session state
    - no Gradio dependencies
    """
    reply = handle_message(req.message)
    return {"reply": reply}
