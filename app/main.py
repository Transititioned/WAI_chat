# ==========================================================
# CaveBot Modular Main
# Version: 0.3.8-dev
# Purpose: Entry point for modularised app, now testing loaders + config
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

    print("🚀 Initialization complete (loader + config test).")
