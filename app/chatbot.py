# ==========================================================
# app/chatbot.py — WorkFriend Chatbot (v2.8 — Compact Above-the-Fold Layout)
# ==========================================================

import gradio as gr
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from pathlib import Path
from app.chatbot_actions import add_feedback_below_chatbot


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
    # 🎨 FINAL COMPACT LAYOUT (Above-the-Fold)
    # ======================================================
    custom_css = """
    /* --- Eliminate extra whitespace above/below --- */
    .gradio-container, .block, .wrap, .gradio-app {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }

    /* --- Chatbot fixed height --- */
    .chatbot-area {
        max-height: 300px !important;
        min-height: 300px !important;
        overflow-y: auto !important;
        border-radius: 6px !important;
        margin-bottom: 6px !important;
    }

    /* --- Input + Send row --- */
    .input-row {
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        margin-top: 4px !important;
        margin-bottom: 4px !important;
    }

    /* --- Main button style --- */
    .wf-btn {
        background-color: #00C4A7 !important;
        color: #fff !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1rem !important;
        cursor: pointer !important;
        transition: background-color 0.2s ease !important;
    }
    .wf-btn:hover {
        background-color: #00A38A !important;
    }

    /* --- Secondary buttons row (Copy/Retry) --- */
    .secondary-row {
        display: flex !important;
        justify-content: flex-end !important;
        gap: 8px !important;
        margin-top: 2px !important;
    }
    """

    # ======================================================
    # 🚀 Gradio UI — final above-the-fold version
    # ======================================================
    theme = gr.themes.Default()
    with gr.Blocks(theme=theme, css=custom_css) as demo:
        gr.Markdown("### 💬 WorkFriend Chatbot")

        chatbot = gr.Chatbot(
            label="WorkFriend Conversation",
            type="messages",
            elem_classes=["chatbot-area"]
        )
        add_feedback_below_chatbot()

        # --- Input row with Send beside textbox ---
        with gr.Row(elem_classes="input-row"):
            user_input = gr.Textbox(
                placeholder="Ask me something...",
                label="Your question:",
                scale=9,
            )
            send_btn = gr.Button("Send", elem_classes=["wf-btn"], scale=1)

        # --- Secondary button row ---
        with gr.Row(elem_classes="secondary-row"):
            retry_btn = gr.Button("↻ Retry Last", elem_classes=["wf-btn"])
            copy_btn = gr.Button("📋 Copy Last Response", elem_classes=["wf-btn"])

        # --- Event bindings ---
        send_btn.click(fn=answer_fn, inputs=[user_input, chatbot], outputs=chatbot)
        retry_btn.click(fn=lambda h: h[:-1], inputs=[chatbot], outputs=chatbot)

        # --- JS: Copy last response ---
        gr.HTML("""
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
                setTimeout(() => { copyBtn.innerText = '📋 Copy Last Response'; }, 1500);
              })
              .catch(() => alert("Clipboard blocked ⚠️"));
          });
        }, 1500);
        </script>
        """)

    print("✅ Chatbot UI built successfully (v2.8 compact).")
    return demo
