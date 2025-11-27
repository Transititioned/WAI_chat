# ==========================================================
# app/chatbot.py — WorkFriend Chatbot (v3.0 + Mobile UX Fix)
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
    # 🎨 Styling (Desktop baseline)
    # ======================================================
    custom_css = """
    .gradio-container *, 
    .gradio-container, 
    .block, 
    .wrap, 
    .gradio-app, 
    .svelte-1ipelgc {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        gap: 0 !important;
    }

    footer, .footer, .svelte-1ipelgc > div:last-child {
        display: none !important;
        height: 0 !important;
    }

    .chatbot-area {
        max-height: 275px !important;
        min-height: 275px !important;
        overflow: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    .chatbot-area > div:not(.gr-label) {
        max-height: 275px !important;
        min-height: 275px !important;
        overflow-y: auto !important;
    }

    .input-controls-row {
        margin-top: -12px !important; 
        padding: 0 !important;
        align-items: flex-end !important;
        gap: 1rem !important;
    }

    .wf-btn, .wf-btn button {
        background-color: #00C4A7 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        height: 38px !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 6px !important;
        cursor: pointer !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1) !important;
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
    """

    # ======================================================
    # 📱 MOBILE-ONLY PATCH (Send beside prompt + feedback spacing fix)
    # ======================================================
    custom_css += """
    @media (max-width: 768px) {

        /* Fix feedback icons clipping */
        .feedback-wrapper {
            padding-bottom: 16px !important;
            position: relative !important;
            z-index: 50 !important;
        }

        .chatbot-area {
            overflow-y: auto !important;
            padding-bottom: 20px !important; /* extra breathing room */
        }

        /* Layout: Prompt (left) | Send (right), Retry below */
        .input-controls-row {
            display: flex !important;
            flex-direction: row !important;
            align-items: flex-end !important;
        }

        .right-controls {
            width: 120px !important;
            flex-direction: column !important;
            gap: 6px !important;
        }

        /* SEND on top */
        .right-controls button:nth-child(2) {
            order: 1 !important;
        }

        /* RETRY below */
        .right-controls button:nth-child(1) {
            order: 2 !important;
        }

        /* Prompt expands to full width */
        .input-controls-row textarea,
        .input-controls-row .gradio-input,
        .input-controls-row .gradio-textbox {
            flex: 1 !important;
        }
    }
    """

    # ======================================================
    # 🚀 Gradio UI
    # ======================================================
    theme = gr.themes.Default()
    with gr.Blocks(theme=theme, css=custom_css) as demo:
        gr.Markdown("### 💬 WorkFriend Chatbot")

        chatbot = gr.Chatbot(
            label="WorkFriend Conversation",
            type="messages",
            height=420,
            elem_classes=["chatbot-area"]
        )

        add_feedback_below_chatbot()

        with gr.Row(elem_classes="input-controls-row"):
            user_input = gr.Textbox(
                placeholder="Ask me something...",
                label="Your question:",
                scale=4
            )

            with gr.Column(elem_classes="right-controls", scale=0):
                copy_btn = gr.Button("📋 Copy Last Response", elem_classes=["wf-btn"], variant="primary")

                actions = add_user_actions(chatbot, retrieve_and_answer)
                retry_btn = actions.get("retry")
                if isinstance(retry_btn, gr.Button):
                    retry_btn.elem_classes = (retry_btn.elem_classes or []) + ["wf-btn"]

                send_btn = gr.Button("Send", elem_classes=["wf-btn"], variant="primary")

        send_btn.click(fn=answer_fn, inputs=[user_input, chatbot], outputs=chatbot)
        user_input.submit(fn=answer_fn, inputs=[user_input, chatbot], outputs=chatbot)

        # Enter / Shift+Enter behaviour
        gr.HTML("""
            <script>
            document.addEventListener("keydown", function (e) {
                const ta = e.target;
                if (!ta || ta.tagName !== "TEXTAREA") return;

                if (e.shiftKey && e.key === "Enter") {
                    e.stopPropagation();
                    return;
                }

                if (!e.shiftKey && e.key === "Enter") {
                    e.preventDefault();
                    e.stopPropagation();
                    const sendBtn = Array.from(
                        document.querySelectorAll("button")
                    ).find(btn => btn.textContent.trim() === "Send");
                    if (sendBtn) sendBtn.click();
                    return false;
                }
            });
            </script>
        """)

    return demo
