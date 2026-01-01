"""
Document structure contracts for the Rehumanizer.

Each structure defines:
- A clear behavioural contract (rules the editor must follow)
- A worked example showing the intended transformation

This file is intentionally content-heavy and logic-free.
"""

STRUCTURES = {

    "get_to_point": {
        "label": "Get to the point",
        "when_to_use": "Commercial writing, LinkedIn posts, emails, recommendations",

        "contract": """
STRUCTURE: Get to the Point

Rules:
- Lead with the main conclusion, decision, or ask in the first 1–2 sentences
- Follow with concise supporting reasoning
- Place background or context last
- Keep the tone confident and decisive
- Avoid bullet points unless they already exist in the input
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
        "label": "Narrative build-up",
        "when_to_use": "Government, policy, briefing notes, formal decision papers",

        "contract": """
STRUCTURE: Narrative Build-Up

Rules:
- Begin with context and framing
- Progress logically through reasoning
- Arrive at the conclusion or recommendation near the end
- Maintain a calm, measured tone
- Avoid direct or bullet-pointed asks
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
        "label": "Executive brief",
        "when_to_use": "Senior leaders, time-poor stakeholders, decision summaries",

        "contract": """
STRUCTURE: Executive Brief

Rules:
- Start with a clear headline sentence that states the core point
- Follow with three short paragraphs (not bullet points)
- Each paragraph should cover one distinct idea
- End with a clear implication or takeaway
- Keep language direct and economical
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
