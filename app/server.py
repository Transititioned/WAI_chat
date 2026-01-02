# app/server.py

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from gradio.routes import mount_gradio_app

from app.bootstrap import bootstrap
from app.api import router as api_router
from app.chatbot import init_chatbot

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
# Root route (keep HF + browsers happy)
# ---------------------------
@app.get("/")
def root():
    # Send users to the Gradio UI path
    return RedirectResponse(url="/chatbot")


# ---------------------------
# Gradio UI
# ---------------------------
demo = init_chatbot()
app = mount_gradio_app(app, demo, path="/chatbot")
