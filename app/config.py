# ==========================================================
# config.py – Environment and directory configuration
# CaveBot Modular Build v0.3.8-dev
# ==========================================================
import os
from pathlib import Path

print("⚙️  Initializing configuration...")

# ==========================================================
# 1. Load API key (robust fallback for Hugging Face)
# ==========================================================
def read_secret_key():
    """Try all known places HF might store secrets."""
    # 1️⃣ Standard env var
    key = os.environ.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if key:
        return key

    # 2️⃣ HF secret files (rare but happens in nested dirs)
    secret_file = "/etc/secrets/OPENAI_API_KEY"
    if os.path.exists(secret_file):
        with open(secret_file, "r") as f:
            return f.read().strip()

    # 3️⃣ Absolute fallback
    return None


OPENAI_KEY = read_secret_key()


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
