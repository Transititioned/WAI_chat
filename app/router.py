# ==========================================================
# app/router.py — WorkFriend Routing Layer (Stable Alpha)
# Safely post-processes answers so WAI can explain thinking
# ==========================================================

import re

# ----------------------------------------------------------
# Detect if user wants reasoning/explanation
# ----------------------------------------------------------
EXPLAIN_TRIGGERS = [
    "why", "explain", "how did you", "reasoning", "thought process",
    "walk me through", "justify", "what's the logic", "how did you arrive",
    "explain your thinking"
]

def needs_explanation(question: str) -> bool:
    q = (question or "").lower()
    return any(t in q for t in EXPLAIN_TRIGGERS)


# ----------------------------------------------------------
# Core processor — now SAFE to call with 1 or 2 args
# ----------------------------------------------------------
def postprocess_answer(question=None, model_answer=None) -> str:
    """
    Flexible signature — prevents crash if called incorrectly.

    Valid calls:
        postprocess_answer(answer_only)
        postprocess_answer(question, answer)
    """
    # If only one arg is passed → treat as raw answer passthrough
    if question and model_answer is None:
        return str(question).strip()

    # If both present → apply reasoning rule
    if question and model_answer:
        if needs_explanation(question):
            return (
                model_answer.strip() +
                "\n\n---\n### 🧠 Reasoning Behind This Answer\n"
                "- Pattern sourced from project alignment framing.\n"
                "- Success defined early prevents downstream drift.\n"
                "- Questions surface assumptions + stakeholder gaps.\n"
                "- If/Then rule anchors decisions to shared success.\n"
            )
        return model_answer.strip()

    # Edge case — absolutely nothing returned from LLM
    return "⚠️ No answer generated."


# ----------------------------------------------------------
# Router wrapper used by chatbot/main
# ----------------------------------------------------------
def route(*args):
    """
    Supports:
        route(answer)
        route(question, answer)
    """
    if len(args) == 1:
        return postprocess_answer(args[0])       # passthrough

    if len(args) == 2:
        return postprocess_answer(args[0], args[1])

    return "⚠️ router.route() called with invalid argument count."


# ----------------------------------------------------------
# Self-test
# ----------------------------------------------------------
if __name__ == "__main__":
    print("\n[router] test:")
    print(route("Plain answer only"))
    print(route("Explain why alignment matters", "Alignment avoids downstream friction."))
