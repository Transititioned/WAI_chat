import os
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# Semantic imports (to be implemented next)
from re_humanizer.prompts.system_intent import SYSTEM_INTENT
from re_humanizer.prompts.structures import STRUCTURES
from re_humanizer.prompts.tones import TONE_MAP


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
