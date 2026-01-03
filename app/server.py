# app/server.py

from fastapi import FastAPI
from gradio.routes import mount_gradio_app

from app.bootstrap import bootstrap
from app.api import router as api_router
from app.chatbot import init_chatbot

# 1. Initialize FastAPI without the root_path (since we are mounting to root)
app = FastAPI(title="WorkFriend WAI")

# ---------------------------
# Startup lifecycle
# ---------------------------
@app.on_event("startup")
def startup():
    bootstrap()

# ---------------------------
# API routes
# ---------------------------
app.include_router(api_router)

# ---------------------------
# Gradio UI
# ---------------------------
# 2. Initialize the chatbot
demo = init_chatbot()

# 3. Mount Gradio to "/" instead of "/chatbot"
# This eliminates the 404/Redirect issues on mobile.
app = mount_gradio_app(app, demo, path="/")