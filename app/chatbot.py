# ==========================================================
# app/chatbot.py — WorkFriend WAI (v4.x)
#
# ARCHITECTURE NOTE:
# ------------------
# The core retrieval + LLM logic is defined at MODULE SCOPE
# so it can be reused by:
#   - Gradio UI (interactive demo)
#   - FastAPI (/chat) endpoint via handle_message()
#
# This keeps the application core UI-agnostic and portable.
#
# IMPORTANT:
# -----------
# This file MUST NOT:
#   - call demo.launch()
#   - import uvicorn
#   - bind ports
#
# Gradio is mounted by FastAPI in server.py
# ==========================================================

import os
from pathlib import Path
import gradio as gr
from gradio.themes import Default, colors

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.chatbot_actions import add_user_actions, add_feedback_below_chatbot
from app.router import route, postprocess_answer


# ==========================================================
# Gradio Theme — Mint Green (Gradio 6 compliant)
# ==========================================================

WAI_THEME = Default(
    primary_hue=colors.emerald,
    secondary_hue=colors.gray,
    neutral_hue=colors.gray,
)


# ==========================================================
# One-time initialisation (shared by UI + API)
# ==========================================================

ARTICLES_DIR = Path("content/articles")
if not ARTICLES_DIR.exists():
    ARTICLES_DIR = Path(".")

openai_key = os.getenv("OPENAI_API_KEY")

embedding = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=openai_key,
)

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.28,
    openai_api_key=openai_key,
)

# ----------------------------------------------------------
# Load markdown corpus into Chroma
# ----------------------------------------------------------

docs = []
for md in ARTICLES_DIR.glob("*.md"):
    txt = md.read_text(encoding="utf-8").strip()
    if not txt:
        continue

    for i in range(0, len(txt), 1500):
        docs.append(
            {
                "content": txt[i:i + 1500],
                "metadata": {"source": md.name},
            }
        )

vectordb = Chroma.from_texts(
    texts=[d["content"] for d in docs],
    embedding=embedding,
    metadatas=[d["metadata"] for d in docs],
)

retriever = vectordb.as_retriever(search_kwargs={"k": 3})


# ==========================================================
# Core retrieval + answer pipeline (APPLICATION CORE)
# ==========================================================

def retrieve_and_answer(q: str) -> str:
    """
    Core retrieval + routing + LLM answer pipeline.
    UI-agnostic. No Gradio, no FastAPI, no session logic.
    """
    lens = route(q)

    docs = retriever.invoke(q)
    context = "\n\n".join(d.page_content for d in docs)

    prompt = ChatPromptTemplate.from_template(
        "{system}\n\nContext:\n{context}\n\n"
        "Respond using:\n"
        "1. **Answer**\n"
        "2. **Why it matters**\n"
        "3. **Plays/Examples**\n\n"
        "User: {q}"
    ).format(
        system=lens,
        context=context,
        q=q,
    )

    res = llm.invoke(prompt)
    return postprocess_answer(res.content)


# ==========================================================
# Public message handler (API + UI entry point)
# ==========================================================

def handle_message(message: str) -> str:
    """
    Stable, UI-agnostic message handler.

    This is the SINGLE entry point used by:
      - FastAPI (/chat)
      - future backend integrations
    """
    return retrieve_and_answer(message)


# ==========================================================
# Gradio UI (presentation layer ONLY)
# ==========================================================

def init_chatbot():
    """
    Builds and returns the Gradio UI.

    NOTE:
    -----
    This function MUST ONLY construct components.
    It must NEVER call demo.launch().
    """

    def answer_fn(msg, history):
        try:
            history = history + [{"role": "user", "content": msg}]
            reply = retrieve_and_answer(msg)
            history = history + [{"role": "assistant", "content": reply}]
            return history, ""
        except Exception as e:
            return history + [{"role": "assistant", "content": f"⚠️ {e}"}], ""

    # ------------------------------------------------------
    # CSS — known-good layout + scroll fix
    # ------------------------------------------------------

    custom_css = """
    footer, .footer { display:none !important; }

    .chatbot-area {
        height: 360px !important;
        overflow: hidden;
    }


    /* FIX: Gradio 6 feedback SVGs are stroke-based, not fill-based */

        button[aria-label="Like"] svg,
        button[aria-label="Dislike"] svg {
        stroke: #666 !important;
        stroke-width: 2 !important;
        opacity: 1 !important;
    }

        button[aria-label="Like"]:hover svg,
        button[aria-label="Dislike"]:hover svg {
        stroke: #00C4A7 !important;
    }






    .chatbot-area > .gr-chatbot {
        height:100% !important;
        overflow-y:auto !important;
        margin:0 !important;
        padding:0 !important;
    }

    .input-controls-row {
        margin-top:12px !important;
        display:flex;
        align-items:flex-end;
        gap:1rem;
    }

    .right-controls {
        width:180px;
        display:flex;
        flex-direction:column;
        gap:8px;
    }

    :root {
        --button-primary-background: #00C4A7 !important;
        --button-primary-background-hover: #00A38A !important;
        --button-primary-text-color: #ffffff !important;
    }

    /* =====================================================
       FIX: SVG up/down vote icons not visible (HF + Gradio 6)
       ===================================================== */

    .wf-feedback-btn svg,
    #wf-feedback-row svg {
        fill: #555 !important;
        opacity: 1 !important;
    }

    .wf-feedback-btn:hover svg,
    #wf-feedback-row button:hover svg {
        fill: #00C4A7 !important;
    }
    """

    with gr.Blocks(theme=WAI_THEME, css=custom_css) as demo:

        gr.Markdown("### 💬 WorkFriend Chatbot")

        chatbot = gr.Chatbot(
            label="WorkFriend Conversation",
            elem_classes=["chatbot-area"],
        )

        add_feedback_below_chatbot()

        with gr.Row(elem_classes="input-controls-row"):

            user_input = gr.Textbox(
                placeholder="Ask WAI...",
                label="Your question:",
                scale=4,
            )

            with gr.Column(elem_classes=["right-controls"], scale=0):

                actions = add_user_actions(chatbot, retrieve_and_answer)

                send_btn = gr.Button("Send")

        send_btn.click(answer_fn, [user_input, chatbot], [chatbot, user_input])
        user_input.submit(answer_fn, [user_input, chatbot], [chatbot, user_input])

        gr.HTML(
            """
            <script>
            document.addEventListener("keydown", function(e){
                if(e.target.tagName==="TEXTAREA" && e.key==="Enter" && !e.shiftKey){
                    e.preventDefault();
                    document.querySelector('button').click();
                }
            });
            </script>
            """
        )

    return demo
