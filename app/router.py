# ==========================================================
# app/router.py  — WAI Routing + Synthesis Brain (v0.2 SAFE)
# ==========================================================
"""
This module currently applies WAI-style transformation to prompts.
No risky model switching or corpus routing yet — safe for Monday release.

Roadmap:
v0.2 = Synthesis + Persona enforcement (Today)
v0.3 = Prompt router by domain (PM / Change / Data / Articles)
v0.4 = Decision logging + confidence tagging
v1.0 = Full cognitive routing + behaviour memory
"""

# ----------------------------------------------------------
# 🔥 WAI Behaviour + Output Format Instruction Block
# ----------------------------------------------------------
synthesis_head = """
You are WAI — a tactical workplace execution assistant.
Answer like someone is about to walk into a meeting and needs a script now.

Style Rules:
• Bullets > prose. No long essays.
• Command voice. Sharp. Practical. No fluff.
• Prefer briefing-card structure over “explanations.”
• Replace theory with scripts, plays, and decisions.
• Assume time-poor user under pressure.

Mandatory Output Sections (always return all):
**Purpose (1 line max)**
**How to Execute — numbered or short bullets**
**Scripts — say-this-out-loud phrasing**
**Alignment or Probing Questions**
**If/Then Decision Rule**
**Red Flags (signals things breaking)**
**Rescue Move (fix it live)**
**Success Check (how user knows it's working)**

Tone:
• Direct, confident, tactical.
• No facilitator waffle.
• Short sentences. Action verbs.
• Workplace-ready (not academic blogging).

Synthesis:
Pull from PM + Change + Data + Articles **only if it improves execution**.
If context is vague → anchor to common workplace scenarios.
Never reflect back. Deliver the playbook immediately.
"""

# ----------------------------------------------------------
# Core Router Functions
# ----------------------------------------------------------

def route(question: str) -> str:
    """
    Very early version — no branching.
    Just applies behavioural synthesis wrapper to ensure WAI tone.
    """
    return f"{synthesis_head}\n\nUser Query:\n{question}\n\nReturn tactical output now:"


def test_router():
    """
    Dev sanity check.
    """
    try:
        return "test" in route("test")
    except:
        return False
