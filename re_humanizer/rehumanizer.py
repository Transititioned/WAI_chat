import os
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# ----------------------------
# Model setup
# ----------------------------

llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0.3,
    openai_api_key=os.environ.get("OPENAI_API_KEY"),
)

# ----------------------------
# Lightweight hygiene pass
# ----------------------------

def basic_cleanup(text: str) -> str:
    """
    Very light, non-semantic cleanup only.
    This should never change meaning.
    """
    text = text.strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.replace("—", "-")
    return text


# ----------------------------
# Prompt components
# ----------------------------

SYSTEM_INTENT = """
You are a professional human editor.

Your job is to rewrite text so it sounds like it was written by a thoughtful,
competent human — not an AI.

Constraints:
- Preserve the author’s intent
- Remove AI clichés, padding, and list-heavy phrasing
- Reduce verbosity without sounding abrupt
- No emojis
- No em dashes
- No “not this, not that” constructions
- Prefer short paragraphs over bullet lists unless explicitly requested
""".strip()


STRUCTURES = {
    "get_to_point": {
        "contract": """
STRUCTURE: Get to the Point

Rules:
- Start with the main ask or conclusion in the first 1–2 sentences
- Follow with brief supporting reasoning
- Background comes last
- Keep it tight and decisive
- Suitable for LinkedIn, email, or commercial settings
""".strip(),
        "example": """
EXAMPLE INPUT:
AI governance is a complex topic with many dimensions. There are benefits and risks,
and organisations need to consider innovation while also being careful.

EXAMPLE OUTPUT:
Organisations need a clear approach to AI governance that balances innovation with safety.
While AI creates real opportunities, unmanaged risk can undermine trust and outcomes.
A practical governance model helps teams move forward confidently without slowing progress.
""".strip(),
    },

    "narrative": {
        "contract": """
STRUCTURE: Narrative Build-Up

Rules:
- Begin with context and framing
- Progress logically through reasoning
- Arrive at the conclusion or recommendation at the end
- Calm, measured tone
- Avoid bullet-point “asks”
""".strip(),
        "example": """
EXAMPLE INPUT:
There are many discussions happening about AI governance right now, and opinions vary.
Some focus on innovation, others on risk.

EXAMPLE OUTPUT:
AI governance is attracting increasing attention as organisations explore new capabilities.
Alongside the opportunities, there is growing awareness of the risks that come with rapid adoption.
A balanced governance approach allows innovation to continue while ensuring safeguards remain in place.
""".strip(),
    },

    "exec_brief": {
        "contract": """
STRUCTURE: Executive Brief

Rules:
- Start with a clear headline sentence
- Follow with 3 short paragraphs (not bullet points)
- Each paragraph covers one key point
- End with a clear implication or takeaway
- Designed for time-poor executives
""".strip(),
        "example": """
EXAMPLE INPUT:
AI governance is important and organisations need to think about it carefully.

EXAMPLE OUTPUT:
AI governance needs to be treated as a strategic capability, not an afterthought.

Effective governance enables innovation by giving teams clarity and confidence.
Without it, risk accumulates quietly and becomes harder to manage later.
Organisations that act early are better positioned to scale AI responsibly.
""".strip(),
    },
}


TONE_MAP = {
    "direct": "Use concise, professional language. Minimal warmth.",
    "professional": "Use a natural professional tone. Neither overly formal nor casual.",
    "conversational": "Use a slightly warmer tone while remaining professional. Do not sound chatty.",
}


# ----------------------------
# Prompt builder
# ----------------------------

def build_prompt(text: str, structure: str, tone: str) -> str:
    if structure not in STRUCTURES:
        raise ValueError(f"Unknown structure: {structure}")

    if tone not in TONE_MAP:
        raise ValueError(f"Unknown tone: {tone}")

    structure_block = STRUCTURES[structure]
    tone_instruction = TONE_MAP[tone]

    prompt = f"""
{SYSTEM_INTENT}

{structure_block['contract']}

{structure_block['example']}

TONE:
{tone_instruction}

Now rewrite the following text:

---
{text}
---
""".strip()

    return prompt


# ----------------------------
# LLM call
# ----------------------------

def call_llm(prompt: str) -> str:
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()


# ----------------------------
# Public API
# ----------------------------

def rehumanize(
    text: str,
    structure: str = "get_to_point",
    tone: str = "professional",
) -> str:
    cleaned = basic_cleanup(text)
    prompt = build_prompt(cleaned, structure, tone)
    return call_llm(prompt)
