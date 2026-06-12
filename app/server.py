# app/server.py
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from gradio.routes import mount_gradio_app

from app.bootstrap import bootstrap
from app.api import router as api_router
from app.chatbot import init_chatbot

# 1. Initialize FastAPI
app = FastAPI(title="WorkFriend WAI")

STATIC_DIR = Path("static")
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 2. Add CORS Middleware (Critical for Cross-Domain Mobile Access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# ---------------------------
# Health Check (The Fix)
# ---------------------------
# Hugging Face's mobile proxy pings "/" to check if the app is ready. 
# Providing this JSON response prevents "Health Check" 404s.
@app.get("/")
def health_check():
    return {"status": "ok", "message": "Workfriend is online"}

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
# 3. Initialize and mount at /chatbot
# This separates the UI from the health check for 100% routing clarity.
demo = init_chatbot()
app = mount_gradio_app(app, demo, path="/chatbot")
