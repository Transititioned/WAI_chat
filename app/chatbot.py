# ==========================================================
# app/chatbot.py — WorkFriend WAI (v4.x)
#
# STABLE UX RESTORE (Dec freeze)
# - Mint green buttons restored
# - Send button inline with textbox
# - Feedback icons visually aligned
#
# Architecture unchanged.
# ==========================================================

import os
from pathlib import Path
import gradio as gr

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.chatbot_actions import add_user_actions, add_feedback_below_chatbot
from app.router import route, postprocess_answer


# ==========================================================
# One-time initialisation (shared by UI + API)
# ==========================================================

ARTICLES_DIR = Path("content/articles")
if not ARTICLES_DIR.exists():
    ARTICLES_DIR = Path(".")

openai_key = os.getenv("OPENAI_API_KEY")

embedding = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=openai_key
)

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.28,
    openai_api_key=openai_key
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
    return retrieve_and_answer(message)


# ==========================================================
# Gradio UI (presentation layer only)
# ==========================================================

def init_chatbot():

    def answer_fn(msg, history):
        try:
            history = history + [{"role": "user", "content": msg}]
            reply = retrieve_and_answer(msg)
            history = history + [{"role": "assistant", "content": reply}]
            return history, ""
        except Exception as e:
            return history + [{"role": "assistant", "content": f"⚠️ {e}"}], ""

    # ------------------------------------------------------
    # CSS — restored working UX
    # ------------------------------------------------------
    custom_css = """
    footer, .footer { display:none !important; }

    .chatbot-area {
        height: 360px !important;
        overflow: hidden;
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
        gap:0.75rem;
    }

    .wf-btn {
        background:#00C4A7 !important;
        color:white !important;
        border-radius:8px !important;
        font-weight:600 !important;
        height:38px;
        min-width:70px;
        display:flex;
        align-items:center;
        justify-content:center;
    }

    .wf-btn:hover {
        background:#00A38A !important;
    }

    /* Feedback icons */
    .feedback-row {
        display:flex;
        justify-content:center;
        gap:14px;
        margin-top:6px;
        opacity:0.6;
    }
    .feedback-row:hover {
        opacity:1;
    }
    """



    








        

     with gr.Blocks(css=custom_css) as demo:

         gr.Markdown("### 💬 WorkFriend Chatbot")
         
        chatbot = gr.Chatbot(
            label="WorkFriend Conversation",
            elem_classes=["chatbot-area"],
        )














        

        # Feedback directly under chat (visual fix only)
        add_feedback_below_chatbot()

        # User action buttons (retry / copy etc) — unchanged
        add_user_actions(chatbot, retrieve_and_answer)

        # --------------------------------------------------
        # Input row — SEND INLINE (ChatGPT-style)
        # --------------------------------------------------
        with gr.Row(elem_classes="input-controls-row"):

            user_input = gr.Textbox(
                placeholder="Ask WAI...",
                label=None,
                scale=8,
            )

            send_btn = gr.Button(
                "Send",
                elem_classes=["wf-btn"],
                scale=1,
            )

        send_btn.click(answer_fn, [user_input, chatbot], [chatbot, user_input])
        user_input.submit(answer_fn, [user_input, chatbot], [chatbot, user_input])

        # Enter-to-send JS (unchanged)
        gr.HTML(
            """
            <script>
            document.addEventListener("keydown", function(e){
                if(e.target.tagName==="TEXTAREA" && e.key==="Enter" && !e.shiftKey){
                    e.preventDefault();
                    document.querySelector('button.wf-btn').click();
                }
            });
            </script>
            """
        )

    return demo
