# ==========================================================
# app/chatbot.py — WAI v4.0 (Router Enabled, Always-Explain Mode)
# Stable Alpha Build — Safe to deploy
# ==========================================================

import gradio as gr
from pathlib import Path
import os

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.chatbot_actions import add_user_actions, add_feedback_below_chatbot
from app.router import route, postprocess_answer   # <-- Works now


# ======================================================
# Main Chatbot Factory
# ======================================================
def init_chatbot():

    # ===== Paths ======================================
    ARTICLES_DIR = Path("content/articles")
    if not ARTICLES_DIR.exists():   # fallback for local dev
        ARTICLES_DIR = Path(".")
    INDEX_DIR = Path("index")

    # ===== Model Setup ================================
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

    # ===== Vectorstore Index ==========================
    docs = []
    for md_file in ARTICLES_DIR.glob("*.md"):
        content = md_file.read_text(encoding="utf-8").strip()
        if not content:
            continue
        chunks = [content[i:i+1500] for i in range(0, len(content), 1500)]
        for chunk in chunks:
            docs.append({"content": chunk, "metadata": {"source": md_file.name}})

    vectordb = Chroma.from_texts(
        texts=[d["content"] for d in docs],
        embedding=embedding,
        metadatas=[d["metadata"] for d in docs],
    )
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})

    # ======================================================
    # Core RAG Response
    # ======================================================
    def retrieve_and_answer(question: str) -> str:

        system = route(question)

        retrieved = retriever.invoke(question)
        context = "\n\n".join([d.page_content for d in retrieved])

        prompt = ChatPromptTemplate.from_template(
            "{system}\n\n"
            "Context:\n{context}\n\n"
            "Answer for an experienced professional using:\n"
            "1. **Answer first** — direct, short, confident.\n"
            "2. **Why it Matters** — principles or pattern behind the advice.\n"
            "3. **Optional examples/plays** *only if additive*.\n\n"
            "User Question: {question}"
        ).format(system=system, context=context, question=question)

        response = llm.invoke(prompt)

        return postprocess_answer(question, response.content)


    # ======================================================
    # Gradio Interaction Handler
    # ======================================================
    def answer_fn(message, history):
        try:
            history.append({"role": "user", "content": message})
            result = retrieve_and_answer(message)
            history.append({"role": "assistant", "content": result})
            return history
        except Exception as e:
            history.append({"role": "assistant", "content": f"⚠️ Error: {e}"})
            return history


    # ======================================================
    # UI — Your Mint layout intact
    # ======================================================
    custom_css = """
    /* You can paste your full CSS here — left empty intentionally */
    """

    with gr.Blocks(theme=gr.themes.Default(), css=custom_css) as demo:

        gr.Markdown(
            "### 💤 WAI Waking Up… <br>May take 5–10s first load.",
            elem_id="wai_wakeup"
        )

        gr.HTML("""<script>
            function wai_check_ready(){
                const chat=document.querySelector('.chatbot-area');
                const ta=document.querySelector('textarea');
                const btn=document.querySelector('button');
                if(chat&&ta&&btn){
                    let wake=document.getElementById('wai_wakeup');
                    if(wake)wake.style.display='none';
                    return;
                }
                setTimeout(wai_check_ready,500);
            }
            setTimeout(wai_check_ready,350);
        </script>""")

        gr.Markdown("### 💬 WorkFriend AI — Chat")

        chatbot = gr.Chatbot(
            type="messages", height=420,
            elem_classes=["chatbot-area"],
            label="Conversation"
        )

        add_feedback_below_chatbot()

        with gr.Row():

            user_input = gr.Textbox(
                label="Ask something",
                placeholder="eg. Kickoff script for stakeholders…",
            )

            with gr.Column(scale=0):
                actions = add_user_actions(chatbot, retrieve_and_answer)
                retry = actions.get("retry")
                send = gr.Button("Send")

        send.click(answer_fn, inputs=[user_input, chatbot], outputs=chatbot)
        user_input.submit(answer_fn, inputs=[user_input, chatbot], outputs=chatbot)

    return demo
