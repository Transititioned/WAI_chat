# ==========================================================
# app/server.py — ASGI composition for Hugging Face
# ==========================================================

from fastapi import FastAPI
from gradio.routes import mount_gradio_app

from app.bootstrap import bootstrap
from app.api import router as api_router
from app.chatbot import init_chatbot

app = FastAPI(title="WorkFriend WAI")


# ----------------------------------------------------------
# Startup lifecycle (THIS replaces main())
# ----------------------------------------------------------

@app.on_event("startup")
def startup():
    bootstrap()


# ----------------------------------------------------------
# API routes
# ----------------------------------------------------------

app.include_router(api_router)


# ----------------------------------------------------------
# Gradio UI
# ----------------------------------------------------------

demo = init_chatbot()
app = mount_gradio_app(app, demo, path="/")
