# ==========================================================
# config.py – Environment and directory configuration
# CaveBot Modular Build v0.3.8-dev
# ==========================================================
import os
from pathlib import Path

print("⚙️  Initializing configuration...")

# ==========================================================
# 1. Load API key (handles Hugging Face Secrets correctly)
# ==========================================================
# Hugging Face injects secrets into the live environment — dotenv not required.
OPENAI_KEY = os.environ.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

if OPENAI_KEY:
    print("✅ OpenAI key loaded successfully.")
else:
    print("⚠️ No OpenAI API key found in environment.")

# ==========================================================
# 2. Directory configuration
# ==========================================================
BASE_DIR = Path(__file__).resolve().parent
CONTENT_DIR = BASE_DIR / "content"
ARTICLES_DIR = CONTENT_DIR / "articles"
INDEX_DIR = BASE_DIR / "index"

for d in [CONTENT_DIR, ARTICLES_DIR, INDEX_DIR]:
    if not d.exists():
        d.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {d}")
    else:
        print(f"📂 Directory exists: {d}")

# ==========================================================
# 3. Debug summary
# ==========================================================
print("[DEBUG] Configuration summary:")
print(f"    BASE_DIR: {BASE_DIR}")
print(f"    CONTENT_DIR: {CONTENT_DIR}")
print(f"    ARTICLES_DIR: {ARTICLES_DIR}")
print(f"    INDEX_DIR: {INDEX_DIR}")
print(f"    OPENAI_KEY: {'YES' if OPENAI_KEY else 'NO'}")

print("⚙️  Configuration initialized successfully.")

# ==========================================================
# 4. Exportable symbols
# ==========================================================
__all__ = [
    "OPENAI_KEY",
    "BASE_DIR",
    "CONTENT_DIR",
    "ARTICLES_DIR",
    "INDEX_DIR",
]
