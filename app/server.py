# app/server.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from gradio.routes import mount_gradio_app

from app.bootstrap import bootstrap
from app.api import router as api_router
from app.chatbot import init_chatbot

# 1. Initialize FastAPI
app = FastAPI(title="WorkFriend WAI")

# 2. Add CORS Middleware 
# This is critical for mobile browsers to successfully handshake 
# with the HF subdomain from your Ghost site.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

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
# 3. Initialize the chatbot
demo = init_chatbot()

# 4. Mount Gradio to "/" 
# Mounting to root is the most stable pattern for mobile routing.
app = mount_gradio_app(app, demo, path="/")