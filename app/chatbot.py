# ========================================================== 
# app/chatbot.py — WorkFriend WAI (v4.x)
# Spinner + Router + Good UX + WakeMsg disabled + Scroll bug fix
# ==========================================================

import gradio as gr
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from pathlib import Path
from app.chatbot_actions import add_user_actions, add_feedback_below_chatbot
from app.router import route, postprocess_answer


def init_chatbot():

    # ------------------------------------------------------
    # Model + Embeddings
    # ------------------------------------------------------
    ARTICLES_DIR = Path("content/articles")
    if not ARTICLES_DIR.exists():
        ARTICLES_DIR = Path(".")
    openai_key = os.getenv("OPENAI_API_KEY")

    embedding = OpenAIEmbeddings(model="text-embedding-3-small",
                                openai_api_key=openai_key)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.28,
                     openai_api_key=openai_key)

    # ------------------------------------------------------
    # Load markdown corpus into Chroma
    # ------------------------------------------------------
    docs = []
    for md in ARTICLES_DIR.glob("*.md"):
        txt = md.read_text(encoding="utf-8").strip()
        if not txt:
            continue
        for i in range(0, len(txt), 1500):
            docs.append({"content": txt[i:i+1500],
                         "metadata": {"source": md.name}})

    vectordb = Chroma.from_texts(
        texts=[d["content"] for d in docs],
        embedding=embedding,
        metadatas=[d["metadata"] for d in docs]
    )
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})

    # ------------------------------------------------------
    # Retrieval + Router aware answer
    # ------------------------------------------------------
    def retrieve_and_answer(q: str):
        lens = route(q)

        docs = retriever.invoke(q)
        context = "\n\n".join([d.page_content for d in docs])

        prompt = ChatPromptTemplate.from_template(
            "{system}\n\nContext:\n{context}\n\n"
            "Respond using:\n"
            "1. **Answer**\n2. **Why it matters**\n3. **Plays/Examples**\n\n"
            "User: {q}"
        ).format(system=lens, context=context, q=q)

        res = llm.invoke(prompt)
        return postprocess_answer(res.content)

    def answer_fn(msg, history):
        try:
            history = history + [{"role": "user", "content": msg}]
            reply = retrieve_and_answer(msg)
            history = history + [{"role": "assistant", "content": reply}]
            return history, ""        # clear input + auto spinner
        except Exception as e:
            return history + [{"role": "assistant", "content": f"⚠️ {e}"}], ""

    # ======================================================
    # CSS — restored design + scroll bug fix
    # ======================================================
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
        gap:1rem;
    }

    .right-controls { width:180px; display:flex; flex-direction:column; gap:8px; }
    .wf-btn { background:#00C4A7 !important; color:white !important;
             border-radius:8px !important; font-weight:600 !important;
             height:38px; display:flex; align-items:center; justify-content:center; }
    .wf-btn:hover { background:#00A38A !important; }

    """

    theme = gr.themes.Default()

    with gr.Blocks(theme=theme, css=custom_css) as demo:

        # Wake message kept for fallback but disabled
        """
        gr.Markdown("### 💤 WAI is waking up… 5–10 sec first use",
                    elem_id="wai_wakeup")
        """

        gr.Markdown("### 💬 WorkFriend Chatbot")

        chatbot = gr.Chatbot(label="WorkFriend Conversation",
                             type="messages",
                             elem_classes=["chatbot-area"])

        add_feedback_below_chatbot()

        with gr.Row(elem_classes="input-controls-row"):

            user_input = gr.Textbox(placeholder="Ask WAI...",
                                    label="Your question:",
                                    scale=4)

            with gr.Column(elem_classes="right-controls", scale=0):

                actions = add_user_actions(chatbot, retrieve_and_answer)

                # ---------------------------------------
                # Only change made — copy button replaced
                # ---------------------------------------
                copy_btn = actions.get("copy")  # <─ working clipboard version

                if "retry" in actions:
                    actions["retry"].elem_classes = ["wf-btn"]

                send_btn = gr.Button("Send", elem_classes=["wf-btn"])

        send_btn.click(answer_fn, [user_input, chatbot], [chatbot, user_input])
        user_input.submit(answer_fn, [user_input, chatbot], [chatbot, user_input])

        gr.HTML("""
        <script>
        document.addEventListener("keydown", function(e){
            if(e.target.tagName==="TEXTAREA" && e.key==="Enter" && !e.shiftKey){
                e.preventDefault();
                document.querySelector('button.wf-btn:last-child').click();
            }
        });
        </script>
        """)

    return demo
