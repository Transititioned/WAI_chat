# ==========================================================
# app/bootstrap.py — Application bootstrap (one-time init)
#
# PURPOSE
# -------
# Runs all heavy / global initialisation exactly once:
#   - loaders
#   - config
#   - vectorstore
#   - LLM engine sanity check
#   - router import
#
# This is called from FastAPI startup events.
# No ports, no UI, no uvicorn, no Gradio.
#
# SAFE TO CALL MULTIPLE TIMES (guarded).
# ==========================================================

import threading

# Simple global guard to prevent double init
_BOOTSTRAP_LOCK = threading.Lock()
_BOOTSTRAPPED = False


def bootstrap():
    global _BOOTSTRAPPED

    if _BOOTSTRAPPED:
        return

    with _BOOTSTRAP_LOCK:
        if _BOOTSTRAPPED:
            return

        print("🧠 Bootstrapping WorkFriend WAI…")

        # --------------------------------------------------
        # Step 1: Loaders
        # --------------------------------------------------
        from . import loaders
        print("✅ Loaders initialised.")

        # --------------------------------------------------
        # Step 2: Config
        # --------------------------------------------------
        from . import config
        print("✅ Config initialised.")

        # --------------------------------------------------
        # Step 3: Vectorstore
        # --------------------------------------------------
        from . import vectorstore
        vectordb = vectorstore.init_vectorstore()
        if vectordb:
            print("🧠 Vectorstore ready.")
        else:
            print("⚠️ Vectorstore returned None.")

        # --------------------------------------------------
        # Step 4: LLM engine test (non-fatal)
        # --------------------------------------------------
        try:
            from . import llm_engine
            ok = llm_engine.test_llm_connection()
            if ok:
                print("🤖 LLM connection OK.")
            else:
                print("⚠️ LLM connection test failed.")
        except Exception as e:
            print("⚠️ LLM engine test skipped:", e)

        # --------------------------------------------------
        # Step 5: Router import (sanity)
        # --------------------------------------------------
        try:
            from . import router
            print("🛣 Router loaded.")
        except Exception as e:
            print("⚠️ Router load issue:", e)

        _BOOTSTRAPPED = True
        print("🚀 Bootstrap complete.")
