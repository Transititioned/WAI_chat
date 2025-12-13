# ==========================================================
# app/server.py — ASGI composition for Hugging Face
#
# This is the SINGLE ASGI entrypoint.
# Hugging Face will auto-detect `app`.
# ==========================================================

from fastapi import FastAPI
from gradio.routes import mount_gradio_app

from app.bootstrap import bootstrap
from app.api import router as api_router
from app.chatbot import init_chatbot


# ----------------------------------------------------------
# FastAPI app
# ----------------------------------------------------------

app = FastAPI(title="WorkFriend WAI")


# ----------------------------------------------------------
# Startup lifecycle (replaces main.py execution)
# ----------------------------------------------------------

@app.on_event("startup")
def on_startup():
    """
    One-time application bootstrap:
    - loaders
    - config
    - vectorstore
    - LLM warm check
    """
    bootstrap()


# ----------------------------------------------------------
# API routes
# ----------------------------------------------------------

app.include_router(api_router)


# ----------------------------------------------------------
# Gradio UI (mounted at /)
# ----------------------------------------------------------

demo = init_chatbot()
mount_gradio_app(app, demo, path="/")
