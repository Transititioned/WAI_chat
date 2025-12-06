# ==========================================================
# app/router.py — WorkFriend Routing Layer (Explain Always Mode)
# WAI always returns: Answer + visible reasoning
# Zero routing complexity — Alpha stable, predictable UX
# ==========================================================

def route(question: str) -> str:
    """
    System prompt injected into every answer.
    Later we can evolve this into multi-mode routing.
    """
    return (
        "You are WAI — WorkFriend AI.\n"
        "• Your users are project/change/data professionals, not juniors.\n"
        "• Respond concisely, directly, but with senior-minded reasoning.\n"
        "• The answer comes first — actionable, not academic.\n"
        "• Then reveal the thinking behind it so the user can sanity-check.\n"
        "• Use alignment, value framing, options, risk, stakeholder patterns.\n"
        "• Tone: collaborative, experienced, never condescending.\n"
    )


def postprocess_answer(question: str, model_answer: str) -> str:
    """
    Wraps the model output with visible reasoning.
    """
    if not model_answer:
        return "⚠️ No model answer returned."

    return (
        model_answer.strip()
        + "\n\n---\n"
        "### 🧠 Why this guidance matters\n"
        "• Shows the decision logic so a senior user can evaluate quality.\n"
        "• Helps compare WAI’s reasoning with their own mental model.\n"
        "• Encourages alignment-first thinking rather than tasks-first.\n"
        "• Reinforces patterns across PM, change, risk and vendor work.\n"
    )


# Manual test (optional)
if __name__ == "__main__":
    print("\n[router] test:", route("test")[:120] + "...")
    print(postprocess_answer("test", "Alignment drives success."))
