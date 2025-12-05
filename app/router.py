# ==========================================================
# app/router.py  -- Routing Brain Stub (Alpha-Safe v0.1)
# ==========================================================

"""
Routing Brain – placeholder for corpus routing and behaviour layer.

Current behaviour (v0.1 - Safe for Release):
------------------------------------------------
• No logic changes to chatbot behaviour
• No influence over prompts or retrieval
• No model-switching
• No risk of hallucination via over-system prompting

Future upgrades (v0.2+):
------------------------------------------------
- Route questions based on domain signals
- Preprocess queries (normalise, detect intent)
- Apply system persona / thinking style
- Add tool choosing + document routing
- Log decisions for AI training + tuning
"""

def route(question: str) -> str:
    """
    Temporary passthrough routing.
    Returns question untouched to maintain Alpha stability.

    v0.2 will add heuristic detection and context tagging.
    """
    return question


def test_router() -> bool:
    """
    Dev sanity check.
    Does NOT affect runtime.
    """
    try:
        return route("test") == "test"
    except Exception:
        return False
