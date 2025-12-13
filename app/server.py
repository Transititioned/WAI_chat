# ==========================================================
# app/server.py — ASGI entrypoint for Hugging Face
# ==========================================================

from fastapi import FastAPI
from gradio.routes import mount_gradio_app

from app.api import api as api_router
from app.chatbot import init_chatbot

# ----------------------------------------------------------
# Create FastAPI app
# ----------------------------------------------------------

app = FastAPI(title="WorkFriend WAI")

# ----------------------------------------------------------
# Include API routes
# ----------------------------------------------------------

app.include_router(api_router)

# ----------------------------------------------------------
# Mount Gradio UI at /
# ----------------------------------------------------------

demo = init_chatbot()
app = mount_gradio_app(app, demo, path="/")
