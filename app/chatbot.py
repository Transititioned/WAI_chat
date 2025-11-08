# ==========================================================
# app/chatbot.py — WorkFriend Chatbot (v1.9 — Unified Buttons, Stable Mint)
# ==========================================================

import gradio as gr
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from pathlib import Path
from app.chatbot_actions import add_user_actions, add_feedback_below_chatbot


def init_chatbot():
    # ------------------------------------------------------
    # Paths and model setup
    # ------------------------------------------------------
    ARTICLES_DIR = Path("content/articles")
    if not ARTICLES_DIR.exists():
        ARTICLES_DIR = Path(".")
    INDEX_DIR = Path("index")

    openai_key = os.getenv("OPENAI_API_KEY")
    embedding = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=openai_key)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, openai_api_key=openai_key)

    # ------------------------------------------------------
    # Vector store build
    # ------------------------------------------------------
    docs = []
    for md_file in ARTICLES_DIR.glob("*.md"):
        text = md_file.read_text(encoding="utf-8").strip()
        if not text:
            continue
        chunks = [text[i:i + 1500] for i in range(0, len(text), 1500)]
        for chunk in chunks:
            docs.append({"content": chunk, "metadata": {"source": md_file.name}})

    vectordb = Chroma.from_texts(
        texts=[d["content"] for d in docs],
        embedding=embedding,
        metadatas=[d["metadata"] for d in docs],
    )
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})

    prompt = ChatPromptTemplate.from_template(
        "Use the following context to answer clearly and concisely:\n\n{context}\n\nQuestion: {question}"
    )

    # ------------------------------------------------------
    # Retrieval + Response
    # ------------------------------------------------------
    def retrieve_and_answer(question: str):
        retrieved_docs = retriever.invoke(question)
        context = "\n\n".join([d.page_content for d in retrieved_docs])
        filled_prompt = prompt.format(context=context, question=question)
        response = llm.invoke(filled_prompt)
        return response.content

    def answer_fn(message, history):
        try:
            history = history + [{"role": "user", "content": message}]
            answer = retrieve_and_answer(message)
            history = history + [{"role": "assistant", "content": answer}]
            return history
        except Exception as e:
            history = history + [{"role": "assistant", "content": f"⚠️ Error: {e}"}]
            return history

    # ======================================================
    # 🎨 Unified Button Styling
    # ======================================================
    custom_css = """
    .wf-btn, .wf-btn button {
        background-color: #00C4A7 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        height: 38px !important;
        min-height: 38px !important;
        width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
        line-height: 1 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 6px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1) !important;
        cursor: pointer !important;
        transition: all 0.2s ease-in-out !important;
    }
    .wf-btn:hover, .wf-btn button:hover {
        background-color: #00A38A !important;
        transform: translateY(-1px);
    }
    .right-controls {
        display: flex !important;
        flex-direction: column !important;
        gap: 8px !important;
        width: 180px !important;
    }
    .input-row {
        display: flex !important;
        align-items: flex-end !important;
        gap: 1rem !important;
    }
    """

    # ======================================================
    # 🚀 Gradio UI
    # ======================================================
    theme = gr.themes.Default()
    with gr.Blocks(theme=theme, css=custom_css) as demo:
        gr.Markdown("### 💬 WorkFriend Chatbot")

        chatbot = gr.Chatbot(label="WorkFriend Conversation", type="messages", height=420)
        add_feedback_below_chatbot()

        with gr.Row(elem_classes="input-row"):
            user_input = gr.Textbox(
                placeholder="Ask me something...",
                label="Your question:",
                scale=4,
            )

            with gr.Column(elem_classes="right-controls"):
                # ✅ Copy button now a real Gradio component
                copy_btn = gr.Button("📋 Copy Last Response", elem_classes=["wf-btn"], variant="primary")

                # Retry + Send
                actions = add_user_actions(chatbot, retrieve_and_answer)
                retry_btn = actions.get("retry")
                if isinstance(retry_btn, gr.Button):
                    retry_btn.elem_classes = (retry_btn.elem_classes or []) + ["wf-btn"]

                send_btn = gr.Button("Send", elem_classes=["wf-btn"], variant="primary")

        # --- Event bindings ---
        send_btn.click(fn=answer_fn, inputs=[user_input, chatbot], outputs=chatbot)

        # --- JS injection to handle copy ---
        gr.HTML(
            """
            <script>
            setTimeout(() => {
              const copyBtn = Array.from(document.querySelectorAll('button'))
                .find(btn => btn.textContent.includes('Copy Last Response'));
              if (!copyBtn) return;
              copyBtn.addEventListener('click', () => {
                const msgs = document.querySelectorAll('.message.bot, .message.assistant');
                if (!msgs.length) return alert("No chatbot response found yet.");
                const txt = msgs[msgs.length - 1].textContent || '';
                navigator.clipboard.writeText(txt)
                  .then(() => {
                    copyBtn.innerText = '✅ Copied!';
                    setTimeout(() => copyBtn.innerText = '📋 Copy Last Response', 1500);
                  })
                  .catch(() => alert("Clipboard blocked ⚠️"));
              });
            }, 1500);
            </script>
            """
        )

    return demo
