import os
import threading
import uvicorn


def start_api():
    """
    Start the FastAPI server in a background thread.

    This exposes a stable /chat endpoint for external clients
    (e.g. Cloudflare Worker) and deliberately runs alongside
    the Gradio UI rather than replacing it.
    """
    try:
        uvicorn.run(
            "app.api:api",
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
    except Exception as e:
        print("❌ Failed to start FastAPI server:", e)


def main():
    print("🧠 Starting CaveBot modular build...")

    # ------------------------------------------------------
    # Step 0: Start FastAPI (background)
    # ------------------------------------------------------
    threading.Thread(target=start_api, daemon=True).start()
    print("🌐 FastAPI server starting in background (port 8000).")

    # ------------------------------------------------------
    # Step 1: Loaders
    # ------------------------------------------------------
    try:
        from . import loaders
        print("✅ Loaders module imported successfully.")
    except Exception as e:
        print("❌ Error importing loaders:", e)
        return

    # ------------------------------------------------------
    # Step 2: Config
    # ------------------------------------------------------
    try:
        from . import config
        print("✅ Config module imported successfully.")
    except Exception as e:
        print("❌ Error importing config:", e)
        return

    # ------------------------------------------------------
    # Step 3: Vectorstore
    # ------------------------------------------------------
    try:
        from . import vectorstore
        print("✅ Vectorstore module imported successfully.")
        vectordb = vectorstore.init_vectorstore()
        if vectordb:
            print("🧠 Vectorstore is ready for use.")
        else:
            print("⚠️ Vectorstore initialization returned None.")
    except Exception as e:
        print("❌ Error importing or initializing vectorstore:", e)

    # ------------------------------------------------------
    # Step 4: LLM Engine Test
    # ------------------------------------------------------
    try:
        from . import llm_engine
        print("✅ LLM Engine module imported successfully.")
        ok = llm_engine.test_llm_connection()
        if ok:
            print("🤖 LLM connection test passed successfully.")
        else:
            print("⚠️ LLM connection test failed.")
    except Exception as e:
        print("❌ Error importing or testing LLM engine:", e)

    # ------------------------------------------------------
    # Step 5: Router sanity load (stub only for now)
    # ------------------------------------------------------
    try:
        from . import router
        print("🛣  Router module imported (stub mode).")
        if hasattr(router, "test_router"):
            router.test_router()
            print("🔍 Router test executed cleanly.")
        else:
            print("ℹ️ Router found, but no test_router() defined yet.")
    except Exception as e:
        print("⚠️ No router module loaded — continuing without routing:", e)

    print("\n🚀 Initialization complete "
          "(loader + config + vectorstore + LLM test + router stub).")

    # ------------------------------------------------------
    # Step 6: Launch Chatbot UI (Gradio)
    # ------------------------------------------------------
    try:
        from . import chatbot
        print("✅ Chatbot module imported successfully.")
        demo = chatbot.init_chatbot()
        print("🚀 Launching CaveBot interface…")
        demo.launch(
            server_name="0.0.0.0",
            server_port=int(os.getenv("PORT", 7860))
        )
    except Exception as e:
        print("❌ Error launching chatbot:", e)
