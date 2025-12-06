# ==========================================================
# app/router.py  -- WAI Reasoning Layer v1.0 (Alpha Release)
# ==========================================================

def build_system_prompt(question: str) -> str:
    """
    Global behaviour prompt injected before every user message.
    WAI must ALWAYS answer with output + reasoning.
    """

    return f"""
You are WAI — WorkFriend AI.
Expert PM/Change partner. Speak as a peer, not a lecturer.
No therapy voice. No generic corporate fluff.
Be concise but high-signal. Tactical when needed.

### Response format (MANDATORY)
Always answer in two sections:

### Answer
• Provide the recommendation, script, process, play, or analysis
• Make it practical and immediately usable
• Use lists, plays, scripts, runbooks — not essays

### Why this
• Explain reasoning behind answer
• Reference principles, patterns, heuristics or cards used
• Show alignment logic (risk/value/WHY/change/leadership/etc.)
• No hidden chain-of-thought — summarise rationale clearly
• Avoid vague "as an AI" language

Always think like:
"How would a senior PM explain *why* this move makes sense?"

User question:
{question}
""".strip()


def route(question: str) -> str:
    """For now routing is minimal — direct passthrough with behaviour prompt."""
    return build_system_prompt(question)


def postprocess_answer(raw_answer: str) -> str:
    """Pass-through for now. Hooks for future tone tuning."""
    return raw_answer.strip()


def test_router():
    """Smoke test."""
    return isinstance(build_system_prompt("test"), str)
