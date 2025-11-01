# ==========================================================
# config.py – Environment and directory configuration
# ==========================================================
import os
from pathlib import Path
from dotenv import load_dotenv

print("⚙️  Initializing configuration...")

# Load .env file if present
load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_KEY:
    print("✅ OpenAI key loaded successfully.")
else:
    print("⚠️ No OpenAI API key found in environment.")

# --- Directory setup ---
ROOT_DIR = Path(__file__).resolve().parent.parent  # project root (above /app)
CONTENT_DIR = ROOT_DIR / "content"
ARTICLES_DIR = CONTENT_DIR / "articles"
INDEX_DIR = ROOT_DIR / "index"

# Create directories if missing
for d in [CONTENT_DIR, ARTICLES_DIR, INDEX_DIR]:
    d.mkdir(parents=True, exist_ok=True)
    print(f"📂 Directory ready: {d}")

# --- Debug summary ---
print("[DEBUG] Configuration summary:")
print(f"    ROOT_DIR: {ROOT_DIR}")
print(f"    CONTENT_DIR: {CONTENT_DIR}")
print(f"    ARTICLES_DIR: {ARTICLES_DIR}")
print(f"    INDEX_DIR: {INDEX_DIR}")
print(f"    OPENAI_KEY: {'YES' if OPENAI_KEY else 'NO'}")

print("⚙️  Configuration initialized successfully.")
