# ==========================================================
# app/router.py — WorkFriend Routing Layer (Alpha Minimal)
# Purpose: Light post-processing so WAI can explain her thinking
# ==========================================================

import re

# ----------------------------------------------------------
# 🔍 Trigger keywords for explanation mode
# ----------------------------------------------------------
EXPLAIN_TRIGGERS = [
    "why",
    "explain",
    "how did you",
    "reasoning",
    "thought process",
    "walk me through",
    "justify",
    "what's the logic",
    "how did you arrive",
    "explain your thinking"
]


def needs_explanation(question: str) -> bool:
    """Return True if user's query asks for reasoning."""
    q = question.lower()
    return any(t in q for t in EXPLAIN_TRIGGERS)


# ----------------------------------------------------------
# 🧠 Core post-processor — called from chatbot.py
# ----------------------------------------------------------
def postprocess_answer(question: str, model_answer: str) -> str:
    """
    Adds a reasoning block IF the user appears to request explanation.
    Default: return answer cleanly.

    Safe alpha behaviour — no re-querying the LLM.
    """
    if not model_answer:
        return "⚠️ No model answer returned."

    # If reasoning was requested
    if needs_explanation(question):
        return (
            model_answer.strip()
            + "\n\n---\n### 🧠 Reasoning Behind This Answer\n"
            "- You asked for thinking, so I'm exposing the rationale.\n"
            "- Guidance is pattern-based: alignment → clarity → risk surfacing.\n"
            "- Answers prioritise shared goals + early risk visibility.\n"
            "- Framework drawn from real PM/Change governance behaviours.\n"
        )

    # Otherwise return the original content cleanly
    return model_answer.strip()


# ----------------------------------------------------------
# 🔁 Compatibility export for main.py (important!)
# Allows: `from app.router import route`
# ----------------------------------------------------------
def route(question: str, model_answer: str) -> str:
    """Alias for postprocess_answer (required by loader)."""
    return postprocess_answer(question, model_answer)


# ----------------------------------------------------------
# Local smoke-test (manual run only)
# ----------------------------------------------------------
if __name__ == "__main__":
    print("\n[router] quick self-test:")

    q1 = "Kickoff tips?"
    a1 = "Success looks like clarity, ownership, and visible priorities."
    print("\nA:", postprocess_answer(q1, a1))

    q2 = "Explain your thinking behind that kickoff guidance"
    a2 = "Success comes from early alignment."
    print("\nB:", postprocess_answer(q2, a2))
