# ==========================================================
# app/router.py — WorkFriend Routing Layer (Alpha Minimal)
# Purpose: Light post-processing so WAI can explain thinking
# ==========================================================

import re

# ----------------------------------------------------------
# Triggers when user *wants reasoning/explanation*
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
    "explain your thinking",
]


def needs_explanation(question: str) -> bool:
    """Returns True if the user is explicitly asking for rationale."""
    q = question.lower()
    return any(t in q for t in EXPLAIN_TRIGGERS)


# ----------------------------------------------------------
# Core function used for expanding answers when requested
# ----------------------------------------------------------
def postprocess_answer(question: str, model_answer: str) -> str:
    """
    If user asks for explanation → append reasoning block.
    If not → return the LLM output unchanged.
    Safe. No rerouting. No second LLM call.
    """
    if not model_answer:
        return "⚠️ No model answer returned."

    if needs_explanation(question):
        return (
            model_answer.strip()
            + "\n\n---\n### 🧠 Reasoning Behind This Answer\n"
              "You asked for explanation, so here's the thinking:\n"
              "- Patterns drawn from project kickoff/alignment principles.\n"
              "- Success framing focuses on shared outcomes + role clarity.\n"
              "- Questions surface assumptions & risks early in delivery.\n"
              "- If/Then rule enforces decision flow anchored to shared goals.\n"
              "- Overall → reduces drift, speeds alignment, avoids rework later.\n"
        )

    return model_answer.strip()


# ----------------------------------------------------------
# 🔁 Compatibility export for main/chatbot integration
# Allows:
#   route(model_answer)
#   route(question, model_answer)
# ----------------------------------------------------------
def route(*args):
    """
    Flexible wrapper so chatbot never crashes from signature mismatch.

    - route(answer)                     → return answer as-is
    - route(question, answer)           → apply reasoning logic if triggered
    """
    if len(args) == 1:
        # Fallback passthrough mode
        return args[0].strip()

    if len(args) == 2:
        question, model_answer = args
        return postprocess_answer(question, model_answer)

    return "⚠️ router.route() called with invalid argument count."


# ----------------------------------------------------------
# Local test mode
# ----------------------------------------------------------
if __name__ == "__main__":
    print("\n[router] Quick self-test:\n")

    print("1) No reasoning expected →")
    print(route("Answer only.\n"))

    print("\n2) Reasoning expected →")
    print(route(
        "Explain why alignment at kickoff matters",
        "Alignment prevents drift + confusion later."
    ))
