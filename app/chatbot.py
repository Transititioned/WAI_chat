# ==========================================================
# app/chatbot.py
# ----------------------------------------------------------
# WorkFriend Chatbot (CaveBot core)
# - LangChain RAG over Markdown corpus
# - Modular user actions: Retry + Copy
# - Inline thumbs-up/down feedback below chatbot output
# - Sandbox-safe inline JS for Hugging Face Spaces
# ==========================================================

import gradio as gr
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from pathlib import Path
from app.chatbot_actions import add_user_actions


def init_chatbot():
    """Initialize and return the Gradio chatbot interface."""
    # --- Paths and setup ---
    ARTICLES_DIR = Path("content/articles")
    if not ARTICLES_DIR.exists():
        ARTICLES_DIR = Path(".")
    INDEX_DIR = Path("index")

    # --- LLM setup ---
    openai_key = os.getenv("OPENAI_API_KEY")
    embedding = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=openai_key)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, openai_api_key=openai_key)

    # --- Build vector store ---
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

    # --- Prompt template ---
    prompt = ChatPromptTemplate.from_template(
        "Use the following context to answer clearly and concisely:\n\n{context}\n\nQuestion: {question}"
    )

    # --- Retrieval & Answer ---
    def retrieve_and_answer(question: str):
        retrieved_docs = retriever.invoke(question)
        context = "\n\n".join([d.page_content for d in retrieved_docs])
        filled_prompt = prompt.format(context=context, question=question)
        response = llm.invoke(filled_prompt)
        return response.content

    # --- Chat handler ---
    def answer_fn(message, history):
        try:
            history = history + [{"role": "user", "content": message}]
            answer = retrieve_and_answer(message)
            history = history + [{"role": "assistant", "content": answer}]
            return history
        except Exception as e:
            history = history + [{"role": "assistant", "content": f"⚠️ Error: {e}"}]
            return history

    # ==========================================================
    # ✅ Gradio Blocks App
    # ==========================================================
    with gr.Blocks() as demo:
        gr.Markdown("### 💬 WorkFriend Chatbot")

        # --- Main Chatbot ---
        chatbot = gr.Chatbot(label="WorkFriend Conversation", type="messages")

        # --- Feedback Section: directly under chatbot output ---
        gr.HTML("""
        <div id="feedback-section" style="text-align:center; margin-top:8px; margin-bottom:6px;">
            <span style="font-size:0.85rem; color:#666;">Did this help?</span><br>
            <button id="thumbs-up"
                style="font-size:1rem; margin:0 8px; background:none; border:none; cursor:pointer; color:#aaa;">
                👍
            </button>
            <button id="thumbs-down"
                style="font-size:1rem; margin:0 8px; background:none; border:none; cursor:pointer; color:#aaa;">
                👎
            </button>
        </div>
        <script>
        setTimeout(() => {
            const up = document.getElementById("thumbs-up");
            const down = document.getElementById("thumbs-down");
            if (up && down) {
                const neutral = "#aaa", good = "#16a34a", bad = "#dc2626";
                up.onclick = () => {
                    up.style.color = good;
                    down.style.color = neutral;
                };
                down.onclick = () => {
                    down.style.color = bad;
                    up.style.color = neutral;
                };
            }
        }, 1000);
        </script>
        """)

        # --- Input Row ---
        with gr.Row():
            user_input = gr.Textbox(
                placeholder="Ask me something...",
                label="Your question:",
                scale=4
            )

            # ==================================================
            # 📦 User Actions Column
            # ==================================================
            with gr.Column(scale=1, min_width=150):
                send_btn = gr.Button("Send", variant="primary")

                # ✅ Modular actions (Retry only)
                actions = add_user_actions(chatbot, retrieve_and_answer)
                retry_btn = actions["retry"]

                # ✅ Inline Copy button now sits neatly under actions
                gr.HTML("""
                <div id="toolbox" style="
                    text-align:center;
                    background:#fafafa;
                    border:1px solid #eee;
                    border-radius:10px;
                    padding:10px;
                    margin-top:12px;
                    box-shadow:0 1px 2px rgba(0,0,0,0.05);">
                    <h5 style="margin-bottom:6px; color:#333;">
                        💼 WorkFriend JS + CSS Toolbox
                    </h5>
                    <button id="copyResponseBtn"
                        style="background:#f97316; color:white; border:none;
                               padding:6px 12px; border-radius:6px;
                               cursor:pointer; font-size:0.9rem;">
                        📋 Copy Last Response
                    </button>
                </div>

                <script>
                setTimeout(() => {
                  const btn = document.getElementById("copyResponseBtn");
                  function getLastBotMessage() {
                    const chatEls = document.querySelectorAll('.message.bot, .message.assistant');
                    if (chatEls.length === 0) return '';
                    const lastEl = chatEls[chatEls.length - 1];
                    return lastEl.textContent || '';
                  }

                  if (btn) {
                    btn.addEventListener("click", () => {
                      const content = getLastBotMessage();
                      if (!content) return alert("No chatbot response found yet.");
                      btn.textContent = "✅ Copied!";
                      navigator.clipboard.writeText(content).then(() => {
                        setTimeout(() => btn.textContent = "📋 Copy Last Response", 1500);
                      }).catch(() => alert("Clipboard blocked ⚠️"));
                    });
                  }
                }, 2000);
                </script>
                """)

        # --- Bind send button ---
        send_btn.click(fn=answer_fn, inputs=[user_input, chatbot], outputs=chatbot)

    return demo
