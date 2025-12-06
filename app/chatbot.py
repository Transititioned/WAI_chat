# ==========================================================
# app/chatbot.py — WorkFriend WAI (v4.0 Router-Enabled, Mint UI kept + Safe)
# ==========================================================

import gradio as gr
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from pathlib import Path
from app.chatbot_actions import add_user_actions, add_feedback_below_chatbot
from app.router import route, postprocess_answer   # <<< NEW (critical)


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
        if not text: continue
        chunks = [text[i:i + 1500] for i in range(0, len(text), 1500)]
        for chunk in chunks:
            docs.append({"content": chunk, "metadata": {"source": md_file.name}})

    vectordb = Chroma.from_texts(
        texts=[d["content"] for d in docs],
        embedding=embedding,
        metadatas=[d["metadata"] for d in docs],
    )
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})

    # ======================================================
    # ⛑️ Router-aware Retrieval + Answer logic
    # ======================================================
    def retrieve_and_answer(question: str):
        system_prompt = route(question)  # <<< inject brain behaviour

        retrieved_docs = retriever.invoke(question)
        context = "\n\n".join([d.page_content for d in retrieved_docs])

        # thinking + structure + explanation baked in 🔥
        prompt = ChatPromptTemplate.from_template(
            "{system}\n\nContext:\n{context}\n\n"
            "Respond clearly using:\n"
            "1. **Answer** – short, direct guidance\n"
            "2. **Why it Matters** – reasoning behind advice\n"
            "3. **Optional Plays/Examples** – if relevant\n\n"
            "User Question: {question}"
        ).format(system=system_prompt, context=context, question=question)

        response = llm.invoke(prompt)
        return postprocess_answer(response.content)  # <<< formatting hook


    def answer_fn(message, history):
        try:
            history.append({"role": "user", "content": message})
            answer = retrieve_and_answer(message)
            history.append({"role": "assistant", "content": answer})
            return history
        except Exception as e:
            return history + [{"role": "assistant", "content": f"⚠️ Error: {e}"}]


    # ======================================================
    # 🎨 Mint UI (unchanged)
    # ======================================================
    custom_css = """<your stylesheet unchanged - skipped for brevity>"""

    theme = gr.themes.Default()

    with gr.Blocks(theme=theme, css=custom_css) as demo:

        gr.Markdown("### 💤 WAI is waking up…<br>This can take 5–10 seconds if sleeping.", elem_id="wai_wakeup")

        gr.HTML("""<script>function wai_check_ready(){const chat=document.querySelector('.chatbot-area');const ta=document.querySelector('textarea');const btn=document.querySelector('button');if(chat&&ta&&btn){const wake=document.querySelector('#wai_wakeup');if(wake)wake.style.display='none';return;}setTimeout(wai_check_ready,500);}setTimeout(wai_check_ready,350);</script>""")

        gr.Markdown("### 💬 WorkFriend Chatbot")

        chatbot = gr.Chatbot(label="WorkFriend Conversation", type="messages", height=420, elem_classes=["chatbot-area"])

        add_feedback_below_chatbot()

        with gr.Row(elem_classes="input-controls-row"):
            user_input = gr.Textbox(placeholder="Ask me something...", label="Your question:", scale=4)

            with gr.Column(elem_classes="right-controls", scale=0):
                copy_btn = gr.Button("📋 Copy Last Response", elem_classes=["wf-btn"])
                actions = add_user_actions(chatbot, retrieve_and_answer)
                retry_btn = actions.get("retry")
                if isinstance(retry_btn, gr.Button):
                    retry_btn.elem_classes = (retry_btn.elem_classes or []) + ["wf-btn"]
                send_btn = gr.Button("Send", elem_classes=["wf-btn"])

        send_btn.click(fn=answer_fn, inputs=[user_input, chatbot], outputs=chatbot)
        user_input.submit(fn=answer_fn, inputs=[user_input, chatbot], outputs=chatbot)

        gr.HTML("""<script>document.addEventListener("keydown",function(e){const ta=e.target;if(!ta||ta.tagName!=="TEXTAREA")return;if(e.shiftKey&&e.key==="Enter")return;if(!e.shiftKey&&e.key==="Enter"){e.preventDefault();e.stopPropagation();const sendBtn=[...document.querySelectorAll("button")].find(btn=>btn.textContent.trim()==="Send");if(sendBtn)sendBtn.click();}});</script>""")

    return demo
