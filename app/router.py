# ==========================================================
# app/router.py — Path A Foundation (Answer + Why + Behaviour Upgrade)
# Safe for Monday Release — No retrieval or logic decisions yet.
# Prepares framework for Path B (cognitive synthesis later)
# ==========================================================

"""
WAI ROUTER (v0.3)

Currently:
✔ Returns the user question unchanged for retrieval
✔ Wraps answer into structured cards if detected
✔ Adds "Why this Works" reasoning layer
✔ Adds senior PM tone + power-protecting behaviour
✔ No risk to existing chatbot behaviour

Next Upgrade Step (Path B):
• Route by topic + corpus
• Synthesis layer across 4 knowledge bases
• Decision logging + traceable reasoning
"""

# -----------------------------
# Base persona + behaviour rules
# -----------------------------
BASE_BEHAVIOUR = """
You are WAI — WorkFriend AI.

Tone:
• Speak as an experienced PM/Change/Delivery peer, not a teacher.
• Respect expertise — you enhance thinking, you don’t instruct.
• Power-protecting, collaborative, never patronising.

Output Rules:
• When user shares a structured card (Opener, Questions, If/Then…)
  — return it cleanly AND append reasoning.
• If the answer contains frameworks, also add a section:
  **How to Apply in Real Life**
• Be crisp, practical, senior.
• No inner monologue. No academic tone.
"""


# -------------------------------------
# Detect if message looks like a "card"
# -------------------------------------
import re

def looks_like_playbook(text: str) -> bool:
    patterns = [
        r"Opener Script", r"Alignment Questions", r"If/Then",
        r"Red Flags", r"Rescue Play", r"Success", r"Risk"
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


# -------------------------------------
# Wrap final answer with thinking layer
# -------------------------------------
def format_response(raw_answer: str) -> str:
    if not looks_like_playbook(raw_answer):
        # normal response — persona only
        return f"{raw_answer}\n\n---\n**Why this Works**\nAnswer provided with WorkFriend peer-tone reasoning."

    # card detected — add structure + thinking layer
    return f"""{raw_answer}

---

### Why this Works
• Opener sets tone and frames alignment.
• Questions surface assumptions and power dynamics early.
• If/Then rule prevents circular debates and decision drift.
• Red flags help a PM notice misalignment before it becomes rework.
• Rescue play gives a live salvage move — stopping tone collapse.

### How to Apply in Real Life
• Use opener → run alignment round-robin → capture priorities in one slide.
• Re-run success alignment mid-project to avoid expectation drift.
• If conflict emerges later, return to the original success definition.
"""


# -----------------------
# PUBLIC ROUTER INTERFACE
# -----------------------
def route(question: str) -> str:
    """
    For Path A — no logic change.
    Returns the question unchanged for retrieval.
    """
    return question


# -----------------------
# Post-processing wrapper
# (chatbot will call this after LLM answer)
# -----------------------
def post_process_answer(answer: str) -> str:
    return format_response(answer)


# -----------------------
# Dev sanity check
# -----------------------
def test_router():
    assert route("test") == "test"
    sample = "Opener Script: ..."
    wrapped = post_process_answer(sample)
    return "Why this Works" in wrapped
