# ==========================================================
# app/router.py  -- Routing + Synthesis Behaviour Stub (v0.21)
# ==========================================================

"""
SAFE FOR ALPHA RELEASE

Routing is still simple — no corpus switching yet.
This version improves answer behaviour without risk:

✔ Keeps current architecture working
✔ No embedding/index code touched
✔ Wraps user question in behaviour framing
✔ Forces actionable format > descriptive narrative
✔ Light synthesis instruction for GPT-4o-mini
"""

# --- Core behaviour style injected into every response ---
synthesis_head = """
You are WAI — a practical workplace assistant.

When answering:
• respond like a senior PM/BA/change practitioner helping on the job
• default to ACTIONABLE output, not theoretical explanation
• get to the point fast — avoid long narrative openings
• always give output using structured formats such as:
  - scripts to say in meetings
  - step-by-step actions
  - decision rules (If X → Then Y)
  - facilitation moves & stakeholder tactics
  - red flags & early warning signals
  - examples or scenario variations
• synthesize across Project Mgmt + Change Mgmt + Data/AI governance where useful
• do not restate definitions — operationalise them
• tone = confident, direct, supportive, workplace pragmatic
"""

# --- Router function (still returns single combined prompt) ---
def route(question: str) -> str:
    """
    Currently: behaviour modifier only.
    Later: routing, classification, memory signals.
    """

    wrapped = f"{synthesis_head}\n\nUser Question:\n{question}\n\nAnswer using structured actionable outputs, not essays."
    return wrapped


# --- Optional sanity test ---
def test_router():
    try:
        out = route("test")
        return isinstance(out, str) and "test" in out.lower()
    except Exception:
        return False
