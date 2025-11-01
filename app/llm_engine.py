# ==========================================================
# llm_engine.py – LLM initialization and test
# CaveBot Modular Build v0.3.8-dev
# ==========================================================

from langchain_openai import ChatOpenAI
from app import config

print("🧠 Initializing LLM engine (debug test mode)...")

# ==========================================================
# 1. Retrieve and normalize API key
# ==========================================================
OPENAI_KEY = config.OPENAI_KEY

api_key = OPENAI_KEY
if callable(api_key):
    # Hugging Face sometimes exposes secrets as async callables
    try:
        api_key = api_key()
    except Exception as e:
        print(f"[DEBUG] API key callable could not be executed directly: {e}")
        api_key = str(api_key)

if not isinstance(api_key, str):
    try:
        api_key = str(api_key)
    except Exception:
        api_key = ""

print(f"[DEBUG] Final OPENAI_KEY type: {type(api_key)}")
print(f"[DEBUG] Key present: {'YES' if api_key else 'NO'}")

# ==========================================================
# 2. Initialize model
# ==========================================================
llm = None
try:
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        openai_api_key=api_key
    )
    print("✅ ChatOpenAI model initialized successfully.")
except Exception as e:
    print(f"❌ LLM initialization failed: {e}")
    llm = None

# ==========================================================
# 3. Run basic test prompt
# ==========================================================
def test_llm_connection():
    """Ping the model with a minimal test prompt for diagnostics."""
    if not llm:
        print("⚠️ LLM not initialized — skipping connection test.")
        return False

    print("[DEBUG] Sending test prompt: Hello! Please respond with a one-line confirmation that the LLM is active.")
    try:
        response = llm.invoke("Hello! Please respond with a one-line confirmation that the LLM is active.")
        print(f"🤖 LLM test response: {response.content if hasattr(response, 'content') else response}")
        print("✅ LLM connection test succeeded.")
        return True
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
        return False


# ==========================================================
# 4. Run connection test on import
# ==========================================================
try:
    test_llm_connection()
except Exception as e:
    print(f"⚠️ LLM connection test failed: {e}")

print("🧠 LLM engine ready (debug mode).")

# ==========================================================
# 5. Exportable symbols
# ==========================================================
__all__ = ["llm", "test_llm_connection"]
