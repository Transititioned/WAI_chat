# ==========================================================
# app/router.py — WorkFriend Routing Layer (B2 Soft Blend)
# ----------------------------------------------------------
# - Scores the user's question against 4 corpora
# - Picks a primary corpus and optional supporting corpus
# - Returns:
#     • system_prompt  (behaviour + explanation contract)
#     • corpora        (list of corpus ids to retrieve from)
#     • primary        (primary corpus id)
#     • label          (human-readable blend label)
# - postprocess_answer() then appends a short lens footer
# ==========================================================

from typing import Dict, List


# -----------------------------
# Corpus configuration
# -----------------------------
CORPORA = {
    "articles": {
        "label": "Strategy & Articles",
        "keywords": [
            "article", "blog", "wai", "workfriend", "portfolio",
            "career", "thought leadership"
        ],
        "base_score": 1.0,  # default fallback when nothing else matches
    },
    "project": {
        "label": "Project Delivery",
        "keywords": [
            "project", "timeline", "schedule", "milestone", "plan",
            "risk register", "raid", "status report", "steerco",
            "go-live", "release", "scope", "dependencies",
            "pm", "pmo", "kickoff", "kick-off"
        ],
        "base_score": 0.0,
    },
    "change": {
        "label": "Change & Stakeholders",
        "keywords": [
            "stakeholder", "adoption", "change", "training",
            "communication", "comms", "resistance", "behaviour",
            "behavioural", "buy-in", "engagement", "leadership",
            "sponsor", "sponsorship", "culture", "alignment"
        ],
        "base_score": 0.0,
    },
    "data": {
        "label": "Data / AI Governance",
        "keywords": [
            "data", "governance", "catalog", "catalogue",
            "databricks", "warehouse", "lakehouse", "etl",
            "pipeline", "dashboard", "reporting", "analytics",
            "model", "ml", "ai", "policy", "standard",
            "vendor", "saas", "integration", "security"
        ],
        "base_score": 0.0,
    },
}

SOFT_BLEND_RATIO = 0.6  # >= 60% of primary score → include as supporting corpus


def _score_corpus(question: str, corpus_id: str) -> float:
    """Very simple keyword scoring for now."""
    q = question.lower()
    cfg = CORPORA[corpus_id]
    score = cfg.get("base_score", 0.0)

    for kw in cfg["keywords"]:
        if kw in q:
            # light weighting – we don't want wild swings
            score += 2.0

    return score


def _pick_corpora(question: str) -> Dict:
    """Return primary + optional supporting corpora based on keyword scores."""
    scores = {cid: _score_corpus(question, cid) for cid in CORPORA.keys()}

    # Choose primary – fall back to "articles" if all zero
    primary = max(scores, key=lambda c: scores[c])
    if all(s <= 0.0 for s in scores.values()):
        primary = "articles"

    primary_score = scores[primary]

    # Soft blend: any other corpus with score >= 60% of primary and > 0
    supporting: List[str] = []
    for cid, s in scores.items():
        if cid == primary:
            continue
        if s > 0.0 and primary_score > 0.0 and s >= primary_score * SOFT_BLEND_RATIO:
            supporting.append(cid)

    corpora = [primary] + supporting if supporting else [primary]

    # Pretty label
    labels = [CORPORA[c]["label"] for c in corpora]
    if len(labels) == 1:
        blend_label = labels[0]
    else:
        blend_label = " + ".join(labels)

    return {
        "primary": primary,
        "corpora": corpora,
        "label": blend_label,
        "scores": scores,
    }


def route(question: str) -> Dict:
    """
    Main entry point used by chatbot.py

    Returns:
      {
        "system_prompt": str,
        "corpora": [corpus_ids],
        "primary": "project" | "change" | "data" | "articles",
        "label": "Project Delivery + Change & Stakeholders"
      }
    """
    blend = _pick_corpora(question)
    corpora = blend["corpora"]
    label = blend["label"]

    # Build a behaviour/system prompt tuned to the blend.
    # Keep it short for mini, but clear about structure.
    focus_bits = []
    if "project" in corpora:
        focus_bits.append("project delivery, risk and practical execution")
    if "change" in corpora:
        focus_bits.append("stakeholder dynamics, leadership behaviour and change adoption")
    if "data" in corpora:
        focus_bits.append("data/AI governance, vendor constraints and technical risk")
    if "articles" in corpora:
        focus_bits.append("your existing WorkFriend articles and patterns")

    focus_text = "; ".join(focus_bits) if focus_bits else "your WorkFriend knowledge base"

    system_prompt = (
        "You are WAI, the WorkFriend assistant. "
        "Answer as if you are a senior practitioner talking to another experienced professional. "
        "Protect their authority: offer options and frames, not commands.\n\n"
        f"For this question, emphasise **{label}** and draw on: {focus_text}.\n\n"
        "Structure every response in three parts:\n"
        "1. **Answer** – concise, high-leverage guidance (no fluff).\n"
        "2. **Why this?** – explain the principles, trade-offs and patterns you are using.\n"
        "3. **Plays / Examples** – 1–3 short scripts, questions or moves they could try.\n"
        "Keep the tone calm, other-focused, and power-protecting."
    )

    blend["system_prompt"] = system_prompt
    return blend


def postprocess_answer(question: str, model_answer: str, routing: Dict | None = None) -> str:
    """
    Light footer so users know which lens WAI used.
    """
    if not model_answer:
        return "⚠️ No model answer returned."

    label = ""
    if routing and routing.get("label"):
        label = routing["label"]

    footer = ""
    if label:
        footer = (
            "\n\n---\n"
            f"_WAI answered using the **{label}** lens. "
            "Use this to cross-check your own judgement rather than as a one-size-fits-all recipe._"
        )

    return model_answer.strip() + footer


# ----------------------------------------------------------
# Optional self-test used by main.py
# ----------------------------------------------------------
def test_router() -> bool:
    try:
        sample_q = "How should I run a project kickoff so stakeholders stay aligned?"
        info = route(sample_q)
        print(f"[router] test primary={info['primary']} corpora={info['corpora']} label={info['label']}")
        return True
    except Exception as e:
        print("[router] test_router error:", e)
        return False


if __name__ == "__main__":
    # Manual quick check
    test_router()
