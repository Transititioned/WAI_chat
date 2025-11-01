# ==========================================================
# CaveBot Modular Main
# Version: 0.3.8-dev
# Purpose: Entry point for modularised app, starting with loaders
# ==========================================================

def main():
    print("🧠 Starting CaveBot modular build...")

    # --- Step 1: Test environment and basic imports ---
    try:
        from . import loaders
        print("✅ Loaders module imported successfully.")
    except Exception as e:
        print("❌ Error importing loaders:", e)
        return

    # --- Step 2: Config ---
    try:
        from . import config
        print("✅ Config module imported successfully.")
    except Exception as e:
        print("❌ Error importing config:", e)
        return

    #try:
        from . import vectorstore
        print("✅ Vectorstore module imported successfully.")
    except Exception as e:
        print("❌ Error importing vectorstore:", e)

    try:
        from . import llm_engine
        print("✅ LLM Engine imported successfully.")
    except Exception as e:
        print("❌ Error importing llm_engine:", e)

    try:
        from . import chatbot_ui
        print("✅ Chatbot UI imported successfully.")
    except Exception as e:
        print("❌ Error importing chatbot_ui:", e)
    """

    print("🚀 Initialization complete (loader test only).")
