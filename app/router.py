# ==========================================================
# app/router.py  -- Routing Brain Stub (Alpha A1)
# ==========================================================
# Foundation for cognitive layer. Safe for Monday release.
# Expands WAI output with reasoning without requiring A2 chain yet.
# ==========================================================

def route(question: str):
    """
    Placeholder routing logic.
    Currently returns the raw question untouched.
    Will later detect topic/corpus/intent & route.
    """
    return question


def postprocess_answer(answer: str) -> str:
    """
    Wraps the answer and forces WAI to EXPLAIN HER THINKING.
    Minimal intervention (safe for alpha).
    - Adds 'Why this works'
    - Adds 'How to apply'
    """
    if not answer:
        return answer

    return (
        answer.strip()
        + "\n\n---\n"
        "🔍 **Why this matters:**\n"
        "This guidance is drawn from structured project/change governance patterns. "
        "It aligns with principle-based delivery (clarity of success, alignment, risk surfacing, "
        "early intervention to avoid silent divergence).\n\n"
        "🧠 **How to apply it live:**\n"
        "Use the script or questions as conversation *frames*, not scripts. "
        "Invite thinking, test assumptions, and observe reactions — silence, disagreement, "
        "or mismatched priorities are signals to pause and realign."
    )


def test_router():
    """
    Basic smoke test to confirm module loads.
    """
    try:
        out = route("test")
        return out == "test"
    except:
        return False
