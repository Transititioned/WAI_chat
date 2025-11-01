# ==========================================================
# CaveBot Modular Main
# ==========================================================

def main():
    print("🧠 Starting CaveBot modular build...")

    # --- Step 1: Loaders ---
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

    # --- Step 3: Vectorstore ---
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

    print("🚀 Initialization complete (loader + config + vectorstore test).")

