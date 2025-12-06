# ================================================================
# app/router.py — WAI Routing v1.0 (Alpha)
# Soft-routing ready, no circular imports
# ================================================================

import re

# ------------------------------------------------
# 1) ROUTING — for now empty (safe default)
# ------------------------------------------------
def route(question: str) -> str:
    """
    Returns an optional system instruction string based on keywords.
    For now returns "" so chatbot works. No imports. No circular risk.
    """
    q = question.lower()

    # simple keyword buckets (B2 soft routing foundation)
    if any(x in q for x in ["ai vendor", "risk", "governance", "data"]):
        return "Use a Data + AI Governance lens."
    if any(x in q for x in ["kickoff", "stakeholder", "change", "alignment"]):
        return "Use a Project Delivery + Stakeholder lens."

    return ""  # neutral default


# ------------------------------------------------
# 2) Postprocess wrapper — keeps your alpha message
# ------------------------------------------------
def postprocess_answer(model_answer: str) -> str:
    """
    Takes final answer text and appends alpha disclaimer exactly as requested.
    """
    return (
        model_answer.strip()
        + "\n\n---\n\nThis is an alpha release. Please check any suggestions given."
    )
