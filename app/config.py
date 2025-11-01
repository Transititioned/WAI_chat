# ==========================================================
# config.py – Environment and directory configuration
# ==========================================================
import os
from pathlib import Path
from dotenv import load_dotenv

print("⚙️  Initializing configuration...")

# --- Load environment variables ---
load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

if OPENAI_KEY:
    print("✅ OpenAI key loaded successfully.")
else:
    print("⚠️ No OpenAI API key found in environment.")

# --- Base and working directories ---
BASE_DIR = Path(__file__).resolve().parent
CONTENT_DIR = BASE_DIR / "content"
ARTICLES_DIR = CONTENT_DIR / "articles"
INDEX_DIR = BASE_DIR / "index"

# --- Ensure directories exist ---
for d in [CONTENT_DIR, ARTICLES_DIR, INDEX_DIR]:
    if not d.exists():
        d.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {d}")
    else:
        print(f"📂 Directory exists: {d}")

# --- Debug summary ---
print("[DEBUG] Configuration summary:")
print(f"    BASE_DIR: {BASE_DIR}")
print(f"    CONTENT_DIR: {CONTENT_DIR}")
print(f"    ARTICLES_DIR: {ARTICLES_DIR}")
print(f"    INDEX_DIR: {INDEX_DIR}")
print(f"    OPENAI_KEY: {'YES' if OPENAI_KEY else 'NO'}")

print("⚙️  Configuration initialized successfully.")
