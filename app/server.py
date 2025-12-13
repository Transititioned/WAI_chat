# app/server.py

from gradio.routes import mount_gradio_app
from app.api import app as fastapi_app
from app.chatbot import init_chatbot

# Build Gradio UI
demo = init_chatbot()

# Compose ASGI app
app = mount_gradio_app(fastapi_app, demo, path="/")
