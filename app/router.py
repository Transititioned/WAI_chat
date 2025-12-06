# ==========================================================
# app/router.py  -- Routing + Behaviour Layer (v0.2 Alpha Safe)
# ==========================================================

"""
This module currently performs light behaviour shaping for WAI.

Why it's safe for release:
• Does not touch vectorstore or retrieval
• Does not change embeddings or DB structure
• No branching logic yet — single path
• Only prepends a system-style instruction to the user question

Goal:
Enhance answer quality by nudging LLM into synthesis mode
(step-by-step, scripts, decision rules, heuristics)

Later upgrades (0.3+):
- corpus routing (PM / Change / Data / Articles)
- decision logging + persona shaping
- chain-of-thought scaffolding
- retrieval weighting
"""


# ----------------------------------------------------------
# Router
# ----------------------------------------------------------

def route(question: str) -> str:
    """
    v0.2 behaviour layer
    — returns question prefixed with a short synthesis instruction

    Style guidance injected:
    • actionable > explanatory
    • practical steps > concepts
    • examples + scripts + heuristics encouraged
    • merge knowledge across PM, Change, Data if relevant
    """

    synthesis_head = """
You are WAI — a practical workplace assistant.

When answering:
• synthesise content into steps, scripts, heuristics & rules of thumb
• avoid generic textbook explanations unless directly asked for them
• prioritise “how to do it tomorrow at work”
• bring in PM + Change + Data governance knowledge if relevant
• when user asks about a concept → turn it into actions, facilitation moves,
  room-behaviour cues, early warning signs, or decision rules
• responses should feel pragmatic, concise, and experience-based
"""

    return synthesis_head + "\n\nUser question: " + question


# ----------------------------------------------------------
# Test Helper (for console confidence)
# ----------------------------------------------------------

def test_router() -> bool:
    try:
        out = route("test-run")
        return "test-run" in out
    except:
        return False
