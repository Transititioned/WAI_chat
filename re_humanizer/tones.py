"""
Tone and formality guidance for the Rehumanizer.

This defines how 'chatty' or formal the rewritten text should feel.
No execution logic lives here.
"""

TONE_MAP = {

    "direct": """
Use concise, professional language.
Prioritise clarity and efficiency over warmth.
Avoid hedging, softeners, or conversational filler.
""".strip(),

    "professional": """
Use a natural professional tone.
Clear, composed, and confident without sounding stiff.
Neither overly formal nor conversational.
""".strip(),

    "conversational": """
Use a slightly warmer tone while remaining professional.
Sound human and approachable, but not casual or chatty.
Avoid slang, jokes, or excessive friendliness.
""".strip(),

}
