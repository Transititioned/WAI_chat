# ==========================================================
# app/router.py  -- WorkFriend Routing + Synthesis Layer v0.1
# Alpha-safe version (no corpus switching or heavy logic yet)
# ==========================================================

"""
Purpose:
    Lightweight routing + behaviour layer to improve answer quality
    without increasing risk for Monday launch.

What it does:
    • Routes question straight through (A1)
    • Adds tone + reasoning expectations (A2)
    • Wraps final answer with short "Why WAI answered this way" reflection
    • No model swaps, no risk — foundation for Phase B intelligent routing

Later (B-upgrade):
    - Select corpus based on intent (PM / Change / Data / Articles)
    - Merge multiple docs → structured synthesis
    - Auto-collect reasoning fingerprint
    - Add behaviour style presets (boss/coach/peer/mentor)
"""

# ----------------------------------------------------------
# Routing — currently pass-through (Base A1 logic)
# ----------------------------------------------------------
def route(question: str) -> str:
    return question  # safe for alpha


# ----------------------------------------------------------
# Build system behaviour wrapper sent *before* answering
# (light layer, no chain-of-thought exposure)
# ----------------------------------------------------------
def apply_behaviour_prompt(question: str) -> str:
    behaviour = """
You are WAI — WorkFriend AI.
Respond as an expert who collaborates with the user, not instructs them.
Avoid teacher tone. Use power-protecting language.
Prefer frameworks, probing questions & alignment scaffolds instead of recipes.

When answering:
• Think in terms of outcomes, alignment & stakeholder reality
• Use the corpus (PM/Change/Data/Articles) where relevant
• Prefer synthesis over generic advice
• Reference cards/heuristics only when useful — not by name
"""
    return behaviour.strip() + "\n\nUser question: " + question


# ----------------------------------------------------------
# Wrap final answer with brief reasoning reflection
# No chain-of-thought, no trace leakage, just rationale summary.
# ----------------------------------------------------------
def apply_explanation_wrapper(final_answer: str, notes: list[str]) -> str:
    notes = notes[:4]  # keep clean & short
    bullet_block = "\n".join(f"• {n}" for n in notes)

    return (
        final_answer.strip()
        + "\n\n---\n### Why WAI responded this way\n"
        + bullet_block
    )


# ----------------------------------------------------------
# Main integration hook for chatbot.py
# (called *after* LLM generates the core answer)
# ----------------------------------------------------------
def postprocess_answer(raw_answer: str, question: str) -> str:
    reasoning_notes = [
        "Used WAI collaborative framing rather than directive tone",
        "Focused answer on alignment not instructions",
        "Selected elements matching the Kickoff/WHY prompt intent",
        "Added practical moves (openers, questions, rescue play)"
    ]
    return apply_explanation_wrapper(raw_answer, reasoning_notes)


# ----------------------------------------------------------
# Dev sanity check
# ----------------------------------------------------------
def test_router():
    try:
        assert route("hello") == "hello"
        return True
    except:
        return False
