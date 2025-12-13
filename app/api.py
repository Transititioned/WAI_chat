# ==========================================================
# app/api.py — FastAPI router for WorkFriend WAI
#
# Thin HTTP adapter over the core chatbot logic.
# - No UI logic
# - No Gradio imports
# - Safe to call from Cloudflare / curl / anything
# ==========================================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.chatbot import handle_message

router = APIRouter(
    prefix="",          # keep paths simple: /chat
    tags=["chat"],
)


# -------------------------
# Request / Response models
# -------------------------

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


# -------------------------
# Chat endpoint
# -------------------------

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Accepts a user message and returns the assistant reply.

    This endpoint is intentionally thin:
    - no session state
    - no UI assumptions
    - delegates directly to core logic
    """
    try:
        reply = handle_message(req.message)
        return {"reply": reply}
    except Exception as e:
        # Never leak stack traces to callers
        raise HTTPException(
            status_code=500,
            detail="Assistant error"
        ) from e


# -------------------------
# Health check (VERY useful)
# -------------------------

@router.get("/health")
async def health():
    return {"status": "ok"}
