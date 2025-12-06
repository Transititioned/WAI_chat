# ==========================================================
# app/router.py — WorkFriend Routing & Synthesis Layer v0.1.1
# ==========================================================
"""
This module handles reasoning + synthesis BEFORE generation.
Designed to be safe for Alpha launch.

Capabilities:
✔ Preprocess question (light touch)
✔ Run synthesis prompt on retrieved context
✔ Enforce WorkFriend tone and practical answers
✔ Drop-in replacement for direct LLM calls

Future Upgrades (not enabled yet):
• Domain routing (PM/Change/Data/Articles)
• Decision logging + model switching
• Weighted retrieval expansion
• Multi-pass chain for synthesis depth
"""

# ----------------------------------------------------------
# Main function called by chatbot.py
# ----------------------------------------------------------

def route(question: str, retriever, llm):
    """Return final WAI-synthesised answer."""
    
    # retrieve top context chunks
    retrieved_docs = retriever.invoke(question)
    context = "\n\n---\n\n".join([d.page_content for d in retrieved_docs])

    # =============================
    # 🔥 WorkFriend Synthesis Layer
    # =============================
    synthesis_prompt = f"""
You are **WAI — WorkFriend**, a practical AI designed for synthesis, not summaries.

Persona:
• Calm, experienced, senior IT/PM advisor voice
• Values clarity, actions, decision rules, signals, risk thinking
• No waffle. No textbook definitions. No corporate mush.
• One answer = something a PM would use today on a real project.

You MUST:
1. Integrate context into insights (not recap it)
2. Turn ideas into steps, heuristics, scripts, or checklists
3. Prefer real-world phrasing over academic language 
4. Add one short example or micro-script if relevant
5. If context is weak → reason using general PM/Change/Data logic safely

Answer Format:
**Insight (1–2 sentences max)**
• Practical guidance (3–5 bullets)
• Mini example or script where suitable

User question: {question}

Context retrieved (imperfect, partial — integrate intelligently):
{context}

Respond as WAI now. Keep final answer clean, helpful, and applied.
"""

    response = llm.invoke(synthesis_prompt)
    return response.content.strip()



# ----------------------------------------------------------
# Simple health check for startup diagnostics
# ----------------------------------------------------------

def test_router():
    try:
        out = route("test", retriever=None, llm=None)  # this will fail intentionally
    except:
        return True  # means function loaded & callable
    return False 
