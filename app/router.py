# ==========================================================
# app/router.py  -- Routing + Synthesis Layer (Alpha-Safe v0.2)
# ==========================================================
"""
Lightweight routing + behaviour layer for WAI.
Safe for Alpha release — retrieval unchanged, no corpus switching yet.

What this file does NOW:
✓ Shapes tone + structure of responses
✓ Instructs LLM to produce scripts, actions, rules
✓ Creates consistent WAI "work execution" style
✓ Pass-through routing (no logic branching yet)

What it will do LATER (v0.3–1.0):
→ route to PM / Change / Data / Articles content
→ behavioral memory + reinforcement
→ decision logging + feedback tuning
→ dynamic prompt enrichment for synthesis across corpora
→ adopt meeting-coach + PM execution persona modes dynamically
"""

# ----------------------------------------------------------
# 🔥 Synthesis Directive (WAI persona + output formatting)
# ----------------------------------------------------------
synthesis_head = """
You are WAI — a workplace execution assistant.

Identity:
• Not academic. Not a coach. You are tactical.
• Your job is to help a PM/leader act effectively in real meetings.

Response Rules:
• Keep outputs sharp, structured, and practical
• No waffle. No high-level consulting fluff.
• Use real workplace language — what someone could say in a meeting today
• Always include at least 3 of the following:
  1) Action steps
  2) If-Then decision rules
  3) Example scripts/phrases
  4) Risks & Red flags
  5) Micro-interventions to fix issues
  6) Variations for different scenarios (optional)
• Write in bullet points > short blocks
• Scripts must be in quotes
• Synthesize across PM + Change Mgmt + Data Governance knowledge when useful
• Priority: clarity → action → confidence

Format Template:
**Title**
• Key bullets
• Action steps
• If/Then rules
• Scripts/examples
• Red flags + rescue moves

Output must feel like a mini playbook — not an essay.
"""


# ----------------------------------------------------------
# Main Route Function (still pass-through for now)
# ----------------------------------------------------------
def route(user_query: str) -> str:
    """
    Takes raw user query, returns formatted directive
    for the LLM prompt. Retrieval is NOT changed yet.
    """
    return f"{synthesis_head}\nUser Query: {user_query.strip()}"


# ----------------------------------------------------------
# Dev sanity check
# ----------------------------------------------------------
def test_router():
    try:
        out = route("test")
        return isinstance(out, str) and "User Query:" in out
    except Exception:
        return False
