# ==========================================================
# app/router.py  -- Routing & Post-Process Foundation (v0.2)
# ==========================================================

"""
Minimal-safe router module for WorkFriend Alpha launch.

Current behaviour (Path A):
  • No semantic routing
  • No rewriting of answers
  • No tone or synthesis
  • Pure passthrough, zero risk

Future behaviour (Path B Upgrade):
  • Intent-based routing to corpus (PM / Change / Data / Articles)
  • Behaviour persona injection (WAI voice, structure, tone)
  • Cross-source synthesis & example generation
  • Decision logging for improvement loop
  • Guardrails for quality and anti-generic output

You can drop new routing/synthesis logic into route() or postprocess_answer()
without touching chatbot UI or vectorstore again.
"""


# ----------------------------------------------------------
# ⛳️ Routing Placeholder
# ----------------------------------------------------------

def route(user_question: str) -> str:
    """
    Current behaviour:
        returns question unchanged.

    Future (Path B):
        - detect project mgmt vs change vs data vs article style queries
        - add lightweight pre-processing
        - tag questions for synthesis
    """
    return user_question


# ----------------------------------------------------------
# 🧠 Post-Processing / Synthesis Placeholder
# ----------------------------------------------------------

def postprocess_answer(answer: str) -> str:
    """
    Current behaviour:
        pass-through (no modification)

    Future (Path B):
        - structure answers into guidance format
        - inject WAI voice style
        - append examples or frameworks if useful
        - cross-pollinate insights across libraries
    """
    return answer


# ----------------------------------------------------------
# 🔍 Sanity Test - optional use in main at startup
# ----------------------------------------------------------

def test_router() -> bool:
    try:
        routed = route("hello")
        post = postprocess_answer("world")
        return routed == "hello" and post == "world"
    except Exception:
        return False
