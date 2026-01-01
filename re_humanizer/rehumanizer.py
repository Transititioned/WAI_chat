from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import os

llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0.3,
    openai_api_key=os.environ.get("OPENAI_API_KEY"),
)


def call_llm(prompt: str) -> str:
    response = llm.invoke([
        HumanMessage(content=prompt)
    ])
    return response.content.strip()


def rehumanize(
    text: str,
    structure: str,      # "get_to_point" | "narrative" | "options"
    formality: str       # "direct" | "professional" | "conversational"
) -> str:
    cleaned = normalize_text(text)
    structured = apply_structure(cleaned, structure)
    toned = apply_formality(structured, formality)
    final = suppress_ai_slop(toned)
    return final

def normalize_text(text: str) -> str:
    return text

def apply_structure(text: str, structure: str) -> str:
    if structure == "get_to_point":
        return restructure_get_to_point(text)
    return text

def apply_formality(text: str, formality: str) -> str:
    return text

def restructure_get_to_point(text: str) -> str:
    prompt = f"""
Rewrite the text below so it follows this structure:

1. Lead with the main point or ask in 1–2 sentences.
2. Follow with concise justification or reasoning.
3. Place background or context last.
4. Preserve the author's intent and meaning.
5. Do NOT add bullet points unless they already exist.
6. Avoid em dashes, clichés, and AI-style phrasing.

Text:
{text}
"""
    return call_llm(prompt)


def suppress_ai_slop(text: str) -> str:
    return text

