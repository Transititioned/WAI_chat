import os
import uvicorn
from gradio.routes import mount_gradio_app

def main():
    print("🧠 Starting CaveBot modular build...")

    # --- Core init (unchanged) ---
    from . import loaders, config, vectorstore, llm_engine, router
    vectorstore.init_vectorstore()
    llm_engine.test_llm_connection()

    print("🚀 Core initialization complete.")

    # --- Compose FastAPI + Gradio ---
    from .api import app as fastapi_app
    from .chatbot import init_chatbot

    demo = init_chatbot()

    # Mount Gradio at /
    app = mount_gradio_app(fastapi_app, demo, path="/")

    print("🌐 API endpoint available at /chat")
    print("💬 UI available at /")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 7860)),
    )
