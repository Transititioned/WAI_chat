# ==========================================================
# app/router.py — WorkFriend Routing Layer (Alpha Minimal)
# Purpose: Light post-processing so WAI explains thinking
# ==========================================================

import re

# ----------------------------------------------------------
# Helper: detect if user is asking for reasoning/explanation
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
    """Check if the user is asking for reasoning."""
    q = question.lower()
    return any(t in q for t in EXPLAIN_TRIGGERS)


# ----------------------------------------------------------
# Main function called from chatbot.py
# ----------------------------------------------------------
def postprocess_answer(question: str, model_answer: str) -> str:
    """
    Adds reasoning/explanation automatically when user requests it.
    If no reasoning requested — return the model response untouched.

    This is ALPHA SAFE: No rerouting, no requerying the LLM.
    """
    if not model_answer:
        return "⚠️ No model answer returned."

    # If user explicitly asked for reasoning
    if needs_explanation(question):
        return (
            model_answer.strip() +
            "\n\n---\n### 🧠 Reasoning Behind This Answer\n"
            "You asked for additional explanation, so here's the thinking:\n"
            "- The response is based on pattern-based project alignment guidance.\n"
            "- Focus is on clarity of success, risk surfacing, and stakeholder coherence.\n"
            "- The structure supports early intervention + shared definition of success.\n"
            "- Applied because misalignment early → downstream failure modes.\n"
        )

    # Default behaviour — clean, normal chat response
    return model_answer.strip()


# ----------------------------------------------------------
# Self-test mode (optional)
# ----------------------------------------------------------
if __name__ == "__main__":
    print("\n[router] quick self-test:")

    q1 = "What does success look like for a kickoff?"
    a1 = "Success looks like clear shared goals and ownership."
    print("\nA:", postprocess_answer(q1, a1))

    q2 = "Explain your reasoning behind this kickoff approach"
    a2 = "Success looks like alignment and shared expectation forming early."
    print("\nB:", postprocess_answer(q2, a2))
