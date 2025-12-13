# app/server.py

from fastapi import FastAPI
from gradio.routes import mount_gradio_app

from app.bootstrap import bootstrap
from app.api import router as api_router
from app.chatbot import init_chatbot

app = FastAPI(title="WorkFriend WAI")

@app.on_event("startup")
async def startup():
    bootstrap()

app.include_router(api_router)

demo = init_chatbot()
mount_gradio_app(app, demo, path="/")
