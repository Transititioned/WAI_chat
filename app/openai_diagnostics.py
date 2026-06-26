# ==========================================================
# app/openai_diagnostics.py
# Lightweight OpenAI API diagnostic checks
# ==========================================================

import os
from openai import OpenAI


def run_openai_diagnostics() -> None:
    openai_key = os.getenv("OPENAI_API_KEY")

    print("=== OPENAI DIAGNOSTICS ===")

    if not openai_key:
        print("❌ OPENAI_API_KEY is missing")
        print("==========================")
        return

    print(f"OPENAI_API_KEY prefix: {openai_key[:12]}")
    print(f"OPENAI_API_KEY suffix: {openai_key[-6:]}")

    client = OpenAI(api_key=openai_key)

    try:
        models = client.models.list()
        print(f"✅ Models API works. Found {len(models.data)} models.")
    except Exception as e:
        print("❌ MODELS FAILED")
        print(repr(e))

    try:
        emb = client.embeddings.create(
            model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            input="hello",
        )
        print("✅ Embeddings work")
        print(f"Embedding preview: {emb.data[0].embedding[:3]}")
    except Exception as e:
        print("❌ EMBEDDINGS FAILED")
        print(repr(e))

    try:
        resp = client.responses.create(
            model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
            input="Say hello",
        )
        print("✅ Responses/chat works")
        print(f"Response preview: {resp.output_text[:80]}")
    except Exception as e:
        print("❌ RESPONSES/CHAT FAILED")
        print(repr(e))

    print("==========================")