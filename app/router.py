# ==========================================================
# app/router.py  (v0.3 – "Answer first / Explain on request")
# ==========================================================
"""
Routing layer – lightweight for Alpha but structured for upgrade path.

Mode C behaviour:
    • Returns a clean direct answer first
    • Stores reasoning for optional reveal
    • If user asks for "why/explain reasoning" → returns both
    • Ready for UI button integration later (no refactor required)

Safe for release. No model switching, no risk to embeddings.
"""

import re

# ------------------------------
# Detect if user requested depth
# ------------------------------
EXPLAIN_TRIGGERS = [
    "why", "explain", "reason", "thinking",
    "walk me through", "what's the rationale",
    "how did you get that"
]

def user_wants_explanation(question: str) -> bool:
    q = question.lower()
    return any(t in q for t in EXPLAIN_TRIGGERS)


# -------------------------------------------
# Core Router – returns structured response
# -------------------------------------------
def route(question: str) -> dict:
    """
    Output format returned to chatbot:
    {
      "answer": string            # main output for user
      "reasoning": string | None  # optional explanation block
    }
    """

    # Base passthrough for now — retrieval happens in chatbot
    clean_q = question.strip()

    # The chatbot will fill these after LLM generation
    return {
        "question": clean_q,
        "answer": None,         # populated by chatbot after retrieve
        "reasoning": None       # attached only if user requests later
    }


# -------------------------------------------
# Post-processing layer (this is where C lives)
# -------------------------------------------
def postprocess_answer(user_question: str, model_answer: str) -> str:
    """
    Splits the answer for Mode C.
    WAI answers normally, but if user requests reasoning —
    we reveal the explanatory portion.
    """
    
    # Detect if explanation was requested this turn
    explain = user_wants_explanation(user_question)

    # Rule:
    # -> If user didn't ask for reasoning → strip explanation section if present
    # -> If they did → return full answer incl. reasoning block

    # Expected formatting pattern (already present from earlier logic):
    # ---------------------
    # <Main Response>
    #
    # 🔍 Why this matters:
    # <Explanation>
    # ---------------------

    if explain:
        return model_answer.strip()

    # Hide explanation by default:
    parts = re.split(r"(?i)(🔍 why this matters:|🧠 why this|why this matters:)", model_answer)
    return parts[0].strip() if parts else model_answer.strip()


# -------------------------------------------
# Router health check
# -------------------------------------------
def test_router() -> bool:
    try:
        sample = route("test")
        return isinstance(sample, dict) and "answer" in sample
    except:
        return False
