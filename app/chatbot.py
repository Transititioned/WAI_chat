# ==========================================================
# app/chatbot.py — WorkFriend Chatbot (Stable Restored Version)
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
    embedding = OpenAIEmbeddings(
        model="text-embedding-3-small", openai_api_key=openai_key
    )
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
    # Prompt + Retrieval
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

    # ------------------------------------------------------
    # Chat Handler
    # ------------------------------------------------------
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
    # Style & Layout
    # ------------------------------------------------------
    theme = gr.themes.Default()
    custom_css = """
    .input-row {
        display: flex;
        align-items: flex-end;
        gap: 1rem;
    }

    .right-controls {
        display: flex;
        flex-direction: column;
        width: 180px;
        gap: 8px;
    }

    .copy-btn {
        background: #00c4b3;
        color: white;
        border: none;
        padding: 10px 0;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 600;
        font-size: 0.95rem;
        transition: background 0.2s ease;
    }
    .copy-btn:hover { filter: brightness(1.1); }

    .gradio-container .gr-chatbot {
        min-height: 450px !important;
        max-height: 70vh !important;
        overflow-y: auto !important;
    }

    .gradio-container .gr-block:has(.feedback-wrapper) {
        margin-bottom: -20px !important;
    }
    """

    # ------------------------------------------------------
    # Gradio App
    # ------------------------------------------------------
    with gr.Blocks(theme=theme, css=custom_css) as demo:
        gr.Markdown("### 💬 WorkFriend Chatbot")

        with gr.Column():
            chatbot = gr.Chatbot(
                label="WorkFriend Conversation",
                type="messages",
                height=450,  # ✅ Comfortable, balanced height
            )

            add_feedback_below_chatbot()

            with gr.Row(elem_classes="input-row"):
                user_input = gr.Textbox(
                    placeholder="Ask me something...",
                    label="Your question:",
                    scale=4,
                )

                with gr.Column(elem_classes="right-controls"):
                    # Copy Button HTML
                    gr.HTML(
                        """
                        <button id="copyResponseBtn" class="copy-btn">
                            📋 Copy Last Response
                        </button>

                        <script>
                        setTimeout(() => {
                          const btn = document.getElementById("copyResponseBtn");
                          if (!btn) return;
                          btn.addEventListener("click", () => {
                            const chats = document.querySelectorAll('.message.bot, .message.assistant');
                            if (!chats.length) return alert("No chatbot response yet.");
                            const last = chats[chats.length - 1];
                            const text = last.textContent.trim();
                            navigator.clipboard.writeText(text);
                            btn.innerHTML = "✅ Copied!";
                            setTimeout(() => { btn.innerHTML = "📋 Copy Last Response"; }, 1500);
                          });
                        }, 1500);
                        </script>
                        """
                    )

                    # Retry and Send
                    actions = add_user_actions(chatbot, retrieve_and_answer)
                    retry_btn = actions.get("retry")
                    send_btn = gr.Button("Send", variant="primary")

        send_btn.click(fn=answer_fn, inputs=[user_input, chatbot], outputs=chatbot)

    return demo
