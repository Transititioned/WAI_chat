# ==========================================================
# app/server.py — ASGI composition for Hugging Face
# ==========================================================

from fastapi import FastAPI
from gradio.routes import mount_gradio_app

from app.api import api as api_router
from app.chatbot import init_chatbot

app = FastAPI(title="WorkFriend WAI")

# Attach API routes
app.include_router(api_router)

# Mount Gradio UI at root
demo = init_chatbot()
app = mount_gradio_app(app, demo, path="/")
