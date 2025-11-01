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

# Set up directories
BASE_DIR = Path(__file__).resolve().parent
ARTICLES_DIR = BASE_DIR / "content" / "articles"
INDEX_DIR = BASE_DIR / "index"

for d in [ARTICLES_DIR, INDEX_DIR]:
    if not d.exists():
        d.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {d}")
    else:
        print(f"📂 Directory exists: {d}")

print("⚙️  Configuration initialized successfully.")
