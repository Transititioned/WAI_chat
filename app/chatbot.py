# ==========================================================
# app/chatbot.py — WorkFriend WAI (v4.x Router + Mint UX)
# Minimal scroll fix applied (no logic changes)
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
    # Paths + Model setup
    # ------------------------------------------------------
    ARTICLES_DIR = Path("content/articles")
    if not ARTICLES_DIR.exists():
        ARTICLES_DIR = Path(".")
    INDEX_DIR = Path("index")

    openai_key = os.getenv("OPENAI_API_KEY")
    embedding = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=openai_key)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.28, openai_api_key=openai_key)

    # ------------------------------------------------------
    # Vector store build (current ARTICLES only for alpha)
    # ------------------------------------------------------
    docs = []
    for md_file in ARTICLES_DIR.glob("*.md"):
        text = md_file.read_text(encoding="utf-8").strip()
        if not text:
            continue
        chunks = [text[i:i+1500] for i in range(0, len(text), 1500)]
        for c in chunks:
            docs.append({"content": c, "metadata": {"source": md_file.name}})

    vectordb = Chroma.from_texts(
        texts=[d["content"] for d in docs],
        embedding=embedding,
        metadatas=[d["metadata"] for d in docs]
    )
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})


    # ------------------------------------------------------
    # Retrieval + Router + Answer
    # ------------------------------------------------------
    def retrieve_and_answer(question: str) -> str:
        system_prompt = route(question)
        retrieved_docs = retriever.invoke(question)
        context = "\n\n".join([d.page_content for d in retrieved_docs])

        prompt = ChatPromptTemplate.from_template(
            "{system}\n\nContext:\n{context}\n\n"
            "Respond using:\n"
            "1. **Answer**\n"
            "2. **Why this matters**\n"
            "3. **Plays / Examples (optional)**\n\n"
            "User Question: {question}"
        ).format(system=system_prompt, context=context, question=question)

        res = llm.invoke(prompt)
        return postprocess_answer(res.content)


    def answer_fn(message, history):
        try:
            history.append({"role": "user", "content": message})
            reply = retrieve_and_answer(message)
            history.append({"role": "assistant", "content": reply})
            return history, ""           # clears textbox
        except Exception as e:
            history.append({"role": "assistant", "content": f"⚠️ Error: {e}"})
            return history, ""


    # ======================================================
    # 🎨 UX + Mint Styling (minimum fix applied here)
    # ======================================================
    custom_css = """
    .gradio-container *, .gradio-container, .block, .wrap, .gradio-app, .svelte-1ipelgc {
        padding-top: 0!important; padding-bottom: 0!important;
        margin-top: 0!important; margin-bottom: 0!important;
        gap: 0!important;
    }
    footer, .footer, .svelte-1ipelgc>div:last-child { display:none!important; }

    /* 🔥 Minimal scroll fix — the key change */
    .chatbot-area {
        max-height: 275px!important;
        min-height: 275px!important;
        overflow-y: auto!important;    /* single scroll layer */
        overflow-x: hidden!important;
        margin: 0!important; padding: 0!important;
    }
    .chatbot-area>div:not(.gr-label){
        max-height: 275px!important;
        min-height: 275px!important;
        overflow-y: auto!important;    /* keeps scroll smooth */
        overflow-x: hidden!important;
    }

    .input-controls-row { margin-top:-12px!important; gap:1rem!important; }

    .wf-btn, .wf-btn *, button.wf-btn { background:#00C4A7!important; color:white!important;
        border:none!important; border-radius:8px!important; font-weight:600!important;
        height:38px!important; width:100%!important; display:flex!important;
        justify-content:center!important; align-items:center!important; gap:6px!important;
    }
    .wf-btn:hover { background:#00A38A!important; }

    .right-controls{ display:flex!important; flex-direction:column!important; gap:8px!important; width:180px!important; }

    @media(max-width:768px){
        .right-controls{ width:120px!important; }
        .right-controls button:nth-child(2){ order:1!important; } /* send on top */
        .right-controls button:nth-child(1){ order:2!important; }
        .input-controls-row textarea{ flex:1!important; }
    }
    """


    # ======================================================
    # 🚀 Build UI
    # ======================================================
    theme = gr.themes.Default()

    with gr.Blocks(theme=theme, css=custom_css) as demo:

        gr.Markdown("### 💤 WAI is waking up… (5–10 seconds first use)", elem_id="wai_wakeup")

        # Hide wake message once UI loads
        gr.HTML("""
        <script>
        function wai_check_ready(){
            const chat=document.querySelector('.chatbot-area');
            const ta=document.querySelector('textarea');
            const btn=document.querySelector('button');
            if(chat&&ta&&btn){
                const w=document.querySelector('#wai_wakeup');
                if(w)w.style.display="none"; return;
            }
            setTimeout(wai_check_ready,400);
        }
        setTimeout(wai_check_ready,350);
        </script>
        """)

        gr.Markdown("### 💬 WorkFriend Chatbot")

        chatbot = gr.Chatbot(label="WorkFriend Conversation", type="messages", height=420, elem_classes=["chatbot-area"])

        add_feedback_below_chatbot()

        with gr.Row(elem_classes="input-controls-row"):
            user_input = gr.Textbox(placeholder="Ask me something...", label="Your question:", scale=4)

            with gr.Column(elem_classes="right-controls"):
                copy_btn = gr.Button("📋 Copy Last Response", elem_classes=["wf-btn"])
                retry = add_user_actions(chatbot, retrieve_and_answer)["retry"]
                retry.elem_classes = ["wf-btn"]
                send_btn = gr.Button("Send", elem_classes=["wf-btn"])

        send_btn.click(fn=answer_fn, inputs=[user_input, chatbot], outputs=[chatbot, user_input])
        user_input.submit(fn=answer_fn, inputs=[user_input, chatbot], outputs=[chatbot, user_input])

        # Enter to send
        gr.HTML("""
        <script>
        document.addEventListener("keydown",e=>{
            const ta=e.target;
            if(ta.tagName!=="TEXTAREA")return;
            if(e.shiftKey&&e.key==="Enter")return;
            if(e.key==="Enter"){e.preventDefault();
                document.querySelector('button.wf-btn:last-of-type').click();}
        });
        </script>
        """)

    return demo
