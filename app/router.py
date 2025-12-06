# ==========================================================
# app/router.py — WorkFriend Routing Layer (Alpha)
# Purpose: Always append reasoning section + required footer
# ==========================================================

def postprocess_answer(model_answer: str) -> str:
    """
    Always enrich model output with reasoning + required alpha footer.
    No conditional logic — predictable UX while corpus grows.
    """

    if not model_answer:
        return "⚠️ No model answer returned."

    # Main answer comes from LLM. We append your mandatory block verbatim.
    return (
        model_answer.strip()
        + "\n\n---\n"
        "This is an alpha release. Please check any suggestions given."
    )


# ----------------------------------------------------------
# FUTURE HOOK: Soft Routing (placeholder — does nothing yet)
# ----------------------------------------------------------
def route(question: str) -> str:
    """
    Path B placeholder for future domain routing.
    Currently returns empty system behaviour so no regressions occur.
    """
    return ""


# ----------------------------------------------------------
# Quick self-test
# ----------------------------------------------------------
if __name__ == "__main__":
    print("\n[router] self-test")
    print(postprocess_answer("Example output for testing."))
    print("\n⤴ Should show answer + alpha footer.\n")
