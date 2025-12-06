# ==========================================================
# app/router.py — WorkFriend Routing Layer (Path A: Explain Always)
# WAI always returns: Answer + Thinking/Reasoning block
# Zero routing complexity — Alpha stable
# ==========================================================

def postprocess_answer(question: str, model_answer: str) -> str:
    """
    Always enrich model output with reasoning.
    (No keyword detection — predictable UX)
    """

    if not model_answer:
        return "⚠️ No model answer returned."

    return (
        model_answer.strip()
        + "\n\n---\n"
        "### 🧠 Why this guidance matters\n"
        "- Based on pattern recognition across PM/change delivery practice.\n"
        "- Focus is on alignment, early risk surfacing, and shared success definition.\n"
        "- Structured to help leaders validate thinking, not just receive instructions.\n"
        "- Reasoning is shown by default so experienced users can evaluate judgement quality.\n"
    )


# Optional manual quick self-test
if __name__ == "__main__":
    print("\n[router] self-test")
    print(postprocess_answer("test", "Success requires alignment early."))
