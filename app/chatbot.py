# ==========================================================
# app/chatbot.py — WorkFriend Chatbot (Final Mint v1.3 — Unified Buttons)
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
    # Paths & Setup
    # ------------------------------------------------------
    ARTICLES_DIR = Path("content/articles")
    if not ARTICLES_DIR.exists():
        ARTICLES_DIR = Path(".")
    INDEX_DIR = Path("index")

    # ------------------------------------------------------
    # LLM Setup
    # ------------------------------------------------------
    openai_key = os.getenv("OPENAI_API_KEY")
    embedding = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=openai_key)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, openai_api_key=openai_key)

    # ------------------------------------------------------
    # Vector Store
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

    # ------------------------------------------------------
    # Prompt Template
    # ------------------------------------------------------
    prompt = ChatPromptTemplate.from_template(
        "Use the following context to answer clearly and concisely:\n\n{context}\n\nQuestion: {question}"
    )

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

    # ------------------------------------------------------
    # 🎨 Scoped CSS — WorkFriend Mint Buttons
    # ------------------------------------------------------
    custom_css = """
    /* === WorkFriend Mint Button Styling === */
    .wf-btn,
    .copy-btn {
        background-color: #00C4A7 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        height: 46px !important;
        width: 100% !important;
        padding: 10px 0 !important;
        text-align: center !important;
        cursor: pointer !important;
        transition: all 0.2s ease-in-out !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 6px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    .wf-btn:hover,
    .copy-btn:hover {
        background-color: #00A38A !important;
        transform: translateY(-1px);
    }

    /* Retry now fully mint, same as Send */
    .wf-btn.wf-retry {
        background-color: #00C4A7 !important;
        color: #ffffff !important;
        border: none !important;
    }
    .wf-btn.wf-retry:hover {
        background-color: #00A38A !important;
    }

    /* Layout consistency */
    .right-controls {
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-end !important;
        gap: 10px !important;
        width: 180px !important;
    }

    .input-row {
        display: flex !important;
        align-items: flex-end !important;
        gap: 1rem !important;
    }
    """

    theme = gr.themes.Default()

    # ------------------------------------------------------
    # 🚀 Gradio Blocks UI
    # ------------------------------------------------------
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
                # Copy Button (HTML)
                gr.HTML(
                    """
                    <button id="copyResponseBtn" class="copy-btn">
                        <span>📋</span> <span>Copy Last Response</span>
                    </button>
                    <script>
                    setTimeout(() => {
                      const btn = document.getElementById("copyResponseBtn");
                      if (!btn) return;
                      function getLastBotMessage() {
                        const msgs = document.querySelectorAll('.message.bot, .message.assistant');
                        if (!msgs.length) return '';
                        return msgs[msgs.length - 1].textContent || '';
                      }
                      btn.addEventListener("click", () => {
                        const txt = getLastBotMessage();
                        if (!txt) return alert("No chatbot response found yet.");
                        navigator.clipboard.writeText(txt)
                          .then(() => {
                            btn.innerHTML = "<span>✅</span> <span>Copied!</span>";
                            setTimeout(() => btn.innerHTML = "<span>📋</span> <span>Copy Last Response</span>", 1500);
                          })
                          .catch(() => alert("Clipboard blocked ⚠️"));
                      });
                    }, 1500);
                    </script>
                    """
                )

                # Action Buttons
                actions = add_user_actions(chatbot, retrieve_and_answer)
                retry_btn = actions.get("retry")
                if isinstance(retry_btn, gr.Button):
                    retry_btn.elem_classes = (retry_btn.elem_classes or []) + ["wf-btn", "wf-retry"]

                send_btn = gr.Button("Send", elem_classes=["wf-btn"], variant="primary")

        send_btn.click(fn=answer_fn, inputs=[user_input, chatbot], outputs=chatbot)

    return demo
