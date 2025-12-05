# ==========================================================
# app/router.py  -- Routing Brain Stub (Alpha-Safe v0.1)
# ==========================================================

"""
This is a minimal placeholder router.

• No logic changes
• No prompt manipulation
• No model switching yet
• Safe to include in Monday release

Later this module will:
- choose corpus (PM / Change / Data / Articles)
- do behaviour shaping
- apply system prompt personality
- log decisions for improvement
"""

def route(question: str):
    """
    For now just returns the raw question.
    Later this will add preprocessing, routing, tagging etc.
    """
    return question


# Optional confidence check for dev-time sanity
def test_router():
    try:
        out = route("test")
        return out == "test"
    except:
        return False
