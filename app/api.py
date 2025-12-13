import os
import uvicorn
from gradio.routes import mount_gradio_app

def main():
    print("🧠 Starting CaveBot modular build...")

    # --- Step 1: Loaders ---
    from . import loaders
    print("✅ Loaders module imported successfully.")

    # --- Step 2: Config ---
    from . import config
    print("✅ Config module imported successfully.")

    # --- Step 3: Vectorstore ---
    from . import vectorstore
    vectordb = vectorstore.init_vectorstore()
    if vectordb:
        print("🧠 Vectorstore is ready for use.")
    else:
        print("⚠️ Vectorstore initialization returned None.")

    # --- Step 4: LLM Engine Test ---
    from . import llm_engine
    ok = llm_engine.test_llm_connection()
    if ok:
        print("🤖 LLM connection test passed successfully.")
    else:
        print("⚠️ LLM connection test failed.")

    # --- Step 5: Router sanity load ---
    from . import router
    print("🛣  Router module imported.")

    print("\n🚀 Core initialization complete.")

    # --------------------------------------------------
    # Step 6: Compose FastAPI + Gradio
    # --------------------------------------------------
    from .api import api               # <-- your FastAPI app
    from .chatbot import init_chatbot  # <-- Gradio UI

    demo = init_chatbot()

    # Mount Gradio at /
    app = mount_gradio_app(api, demo, path="/")

    print("🌐 API endpoint available at /chat")
    print("💬 UI available at /")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 7860)),
    )
