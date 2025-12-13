# ==========================================================
# app.py — Hugging Face Classic SDK entrypoint (SHIM)
#
# IMPORTANT:
# - Required by HF to build & run
# - Must expose a Gradio demo object
# - NO uvicorn
# - NO FastAPI mounting here
#
# This file exists ONLY to satisfy HF Classic runtime.
# ==========================================================

print("🟢 [HF] app.py loaded (classic Gradio shim)")

from app.chatbot import init_chatbot

# HF looks for a variable named `demo`
demo = init_chatbot()

print("🟢 [HF] demo created and exposed")
