# ==========================================================
# app/router.py — Soft Routing Layer (B2 Baseline)
# ==========================================================

# --- keyword buckets for routing ---
ROUTE_MAP = {
    "project":      "project_mgmt",
    "kickoff":      "project_mgmt",
    "timeline":     "project_mgmt",
    "milestone":    "project_mgmt",

    "change":       "change_mgmt",
    "resistance":   "change_mgmt",
    "adoption":     "change_mgmt",
    "stakeholder":  "change_mgmt",

    "data":         "data_gov",
    "quality":      "data_gov",
    "metadata":     "data_gov",

    "ai vendor":    "gov_ai",
    "governance":   "gov_ai",
    "risk":         "gov_ai",
    "security":     "gov_ai",
    "privacy":      "gov_ai"
}

def route(question: str) -> str:
    """
    Soft routing — determines the *thinking lens*,
    NOT the file system. Corpus still global for now.
    """

    q = question.lower()

    for k, lens in ROUTE_MAP.items():
        if k in q:
            return f"Use the **{lens} lens** when answering. Respond practically."

    # fallback
    return "Use general PM/leadership reasoning. Be helpful, concise and pragmatic."


def postprocess_answer(model_answer: str) -> str:
    """
    Appends your EXACT wording disclaimer every time.
    """

    if not model_answer:
        return "⚠️ No model answer returned."

    return (
        model_answer.strip()
        + "\n\n---\n"
        "⚠️ *WAI Alpha Release:* Please check any suggestions given."
    )


# Optional self-test
if __name__ == "__main__":
    print(route("How do I manage stakeholders?"))
    print(postprocess_answer("Example answer"))
