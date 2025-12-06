# ==========================================================
# app/router.py — Soft Routing (B2)
# Routes only by *lens emphasis*, not folder scanning.
# All answers return with reasoning AND alpha disclaimer.
# ==========================================================

def route(question: str) -> str:
    """
    Lightweight router: adjusts lens emphasis only.
    Does NOT control retrieval sources yet — B2 step.
    """

    q = question.lower()

    # --- Keyword lens detection ---
    if any(k in q for k in ["ai vendor", "governance", "risk", "security", "privacy", "data retention"]):
        return (
            "Respond using a Data & AI Governance lens.\n"
            "Focus on controls, transparency, contracts, risk & assurance.\n"
            "Keep tone practical and step-based. Senior stakeholder mindset."
        )

    if any(k in q for k in ["kickoff", "scope", "timeline", "estimation", "deliverable", "pm", "project"]):
        return (
            "Respond using a Project Delivery lens.\n"
            "Focus on clarity, alignment, sequencing and decision flow.\n"
            "Bias toward outcomes, ownership and success criteria."
        )

    if any(k in q for k in ["stakeholder", "change", "adoption", "resistance", "training"]):
        return (
            "Respond using a Change & People lens.\n"
            "Balance empathy with momentum. Ask alignment questions.\n"
            "Use plays, scripts, questions, engagement techniques."
        )

    # default fallback
    return (
        "General response mode. Provide structured answer with reasoning.\n"
        "When uncertain, suggest options + questions to clarify intent."
    )


def postprocess_answer(model_answer: str) -> str:
    """
    Formatting wrapper for all chatbot responses.
    Alpha-stage safety note included (exact wording requested).
    """

    if not model_answer:
        return "⚠️ No model answer returned."

    return (
        model_answer.strip()
        + "\n\n---\n"
        "⚠️ *WAI is in early alpha.*\n"
        "Please check any suggestions against your own judgement."
    )


# Optional local test
if __name__ == "__main__":
    print(postprocess_answer("Test output OK."))
