from fastapi import FastAPI
from gradio.routes import mount_gradio_app

print("🟢 [DEBUG] server.py imported")

from app.bootstrap import bootstrap
from app.api import router as api_router
from app.chatbot import init_chatbot

print("🟢 [DEBUG] imports resolved")

app = FastAPI(title="WorkFriend WAI")
print("🟢 [DEBUG] FastAPI app created:", app)

@app.on_event("startup")
async def startup():
    print("🟢 [DEBUG] FastAPI startup event fired")
    bootstrap()

print("🟢 [DEBUG] registering API router")
app.include_router(api_router)

print("🟢 [DEBUG] building Gradio UI")
demo = init_chatbot()
print("🟢 [DEBUG] demo returned:", demo)

print("🟢 [DEBUG] mounting Gradio at /")
mount_gradio_app(app, demo, path="/")
print("🟢 [DEBUG] mount_gradio_app completed")
