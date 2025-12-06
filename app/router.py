# ==========================================================
# app/router.py — Behaviour Overlay + Light Synthesis (A1+A2)
# Safe for Alpha Release — No architecture risk
# ==========================================================

"""
Routing + Behaviour Layer v0.2

Goals:
• Keep core architecture unchanged
• Shape WAI’s output into action-ready, PM+Change hybrid tone
• Add lightweight synthesis (blend: PM + Change + Articles)
• Enforce WorkFriend answer format + persona
• Zero risk to vectorstore or chatbot runtime

This module is upstream only. It modifies the user query before sending to LLM.
Later versions (B-series) will add corpus-aware routing + multi-prompt maps.
"""

# ----------------------------------------------------------
# 🧠 Personality & Output-Framing Prompt
# Injected into every query before it reaches the model.
# ----------------------------------------------------------

BEHAVIOUR_OVERLAY = """
You are WAI (WorkFriend AI) — practical, sharp, calm and field-tested.
Your job is not to explain theory — it is to tell the user **what to DO next**.

When answering:
• be concise but high-signal
• convert abstract advice into scripts, plays, steps or decision logic
• favour alignment, resistance handling, risk, value and communication
• reference BOTH project management AND change management thinking
• include examples or moves that could work in real meetings
• sound like a senior PM/Change operator sitting beside the user

Format output using this structure:

**🎯 Core Answer (1–3 sentences max)**  
— The essence. No throat clearing.

**How to Run It**  
1. Step
2. Step
3. Step

**If/Then Decision Rule**  
If X happens → respond with Y.

**Signals / Red Flags to Watch For**  
• bullet  
• bullet

**Micro-Rescue Play**  
A short phrase or facilitation move to recover momentum.

Keep tone practical and behaviour-driven.
Avoid generic textbook explanations unless asked.
"""

# ----------------------------------------------------------
# Light Synthesis Layer (A2)
# ----------------------------------------------------------
# Subtle nudge — encourages cross-domain reasoning without forcing it.
# Makes answers WAI-flavoured rather than GPT-generic.

SYNTHESIS_HINT = """
Where relevant, draw links between:
• project initiation, risk & alignment → Kerzner PM patterns
• stakeholder resistance, signals & recovery → Change Mgmt corpus
• templates, plays, checklists → Articles folder content
Do not mention this hint explicitly in answers.
"""


# ----------------------------------------------------------
# Main routing hook used by chatbot
# ----------------------------------------------------------

def route(question: str) -> str:
    """
    Adds behaviour overlay + synthesis hint in prompt prefix.
    Does NOT alter question meaning.
    Safe for alpha release — zero regression risk.
    """

    routed_prompt = f"""
{BEHAVIOUR_OVERLAY.strip()}

{SYNTHESIS_HINT.strip()}

User Question:
{question.strip()}
"""

    return routed_prompt


# ----------------------------------------------------------
# Dev-sanity check (optional)
# ----------------------------------------------------------

def test_router():
    try:
        out = route("test query")
        return "WAI" in out and "How to Run It" in out
    except:
        return False
