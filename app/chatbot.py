# ==========================================================
# app/chatbot.py — WorkFriend WAI (v4.1 Soft-Routed, Mint UI)
# ==========================================================

import os
from pathlib import Path

import gradio as gr
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.chatbot_actions import add_user_actions, add_feedback_below_chatbot
from app.router import route, postprocess_answer


def init_chatbot():
    # ------------------------------------------------------
    # Paths + Model setup
    # ------------------------------------------------------
    BASE_CONTENT = Path("content")

    CORPUS_DIRS = {
        "articles": BASE_CONTENT / "articles",
        "project": BASE_CONTENT / "wai_project_mgmt",
        "change": BASE_CONTENT / "wai_change_mgmt_library",
        "data": BASE_CONTENT / "data_mgmt_library",
    }

    INDEX_DIR = Path("index")

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

    # ------------------------------------------------------
    # Vector store build (all corpora, tagged by `corpus`)
    # ------------------------------------------------------
    docs = []

    for corpus_id, folder in CORPUS_DIRS.items():
        if not folder.exists():
            continue
        for md_file in folder.rglob("*.md"):
            text = md_file.read_text(encoding="utf-8").strip()
            if not text:
                continue
            chunks = [text[i:i + 1500] for i in range(0, len(text), 1500)]
            for chunk in chunks:
                docs.append(
                    {
                        "content": chunk,
                        "metadata": {
                            "source": md_file.name,
                            "corpus": corpus_id,
                        },
                    }
                )

    vectordb = Chroma.from_texts(
        texts=[d["content"] for d in docs],
        embedding=embedding,
        metadatas=[d["metadata"] for d in docs],
        persist_directory=str(INDEX_DIR),
    )

    # Base prompt template – system text is injected per call
    base_prompt = ChatPromptTemplate.from_template(
        "{system}\n\n"
        "Context from your notes and libraries:\n"
        "{context}\n\n"
        "Now respond using the structure above.\n\n"
        "User Question: {question}"
    )

    # ======================================================
    # ⛑️ Router-aware Retrieval + Answer logic
    # ======================================================
    def retrieve_and_answer(question: str) -> str:
        # 1) Ask router which corpora + behaviour to use
        routing = route(question)
        system_prompt = routing["system_prompt"]
        corpora = routing.get("corpora") or ["articles"]

        # 2) Build a filter for Chroma so we only search those corpora
        if len(corpora) == 1:
            search_filter = {"corpus": corpora[0]}
        else:
            search_filter = {"corpus": {"$in": corpora}}

        retriever = vectordb.as_retriever(
            search_kwargs={
                "k": 4,
                "filter": search_filter,
            }
        )

        retrieved_docs = retriever.invoke(question)
        context = "\n\n".join([d.page_content for d in retrieved_docs]) or "No specific notes were retrieved."

        filled_prompt = base_prompt.format(
            system=system_prompt,
            context=context,
            question=question,
        )

        response = llm.invoke(filled_prompt)
        final_text = postprocess_answer(question, response.content, routing)
        return final_text

    def answer_fn(message, history):
        try:
            history = history + [{"role": "user", "content": message}]
            answer = retrieve_and_answer(message)
            history = history + [{"role": "assistant", "content": answer}]
            return history
        except Exception as e:
            return history + [{"role": "assistant", "content": f"⚠️ Error: {e}"}]

    # ======================================================
    # 🎨 Styling (including mint button override)
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

    /* -----------------------------------------
       🍃 WorkFriend Mint Buttons (Brand Override)
    ------------------------------------------ */
    .wf-btn,
    .wf-btn *,
    button.wf-btn,
    button.wf-btn:hover {
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
    .wf-btn:hover {
        background-color: #00A38A !important;
        transform: translateY(-1px) !important;
    }

    .right-controls {
        display: flex !important;
        flex-direction: column !important;
        gap: 8px !important;
        width: 180px !important;
    }

    @media (max-width: 768px) {
        .feedback-wrapper { padding-bottom: 16px !important; position: relative !important; z-index: 50 !important; }
        .chatbot-area { overflow-y: auto !important; padding-bottom: 20px !important; }
        .input-controls-row { flex-direction: row !important; align-items: flex-end !important; }
        .right-controls { width: 120px !important; flex-direction: column !important; gap: 6px !important; }
        .right-controls button:nth-child(2) { order: 1 !important; }
        .right-controls button:nth-child(1) { order: 2 !important; }
        .input-controls-row textarea,
        .input-controls-row .gradio-input,
        .input-controls-row .gradio-textbox { flex: 1 !important; }
    }
    """

    # ======================================================
    # 🚀 Gradio UI
    # ======================================================
    theme = gr.themes.Default()

    with gr.Blocks(theme=theme, css=custom_css) as demo:

        gr.Markdown(
            "### 💤 WAI is waking up…<br>This can take 5–10 seconds if sleeping.",
            elem_id="wai_wakeup",
        )

        gr.HTML("""
        <script>
        function wai_check_ready() {
            const chat = document.querySelector('.chatbot-area');
            const ta   = document.querySelector('textarea');
            const btn  = document.querySelector('button');
            if (chat && ta && btn) {
                const wake = document.querySelector('#wai_wakeup');
                if (wake) wake.style.display = "none";
                return;
            }
            setTimeout(wai_check_ready, 500);
        }
        setTimeout(wai_check_ready, 350);
        </script>
        """)

        gr.Markdown("### 💬 WorkFriend Chatbot")

        chatbot = gr.Chatbot(
            label="WorkFriend Conversation",
            type="messages",
            height=420,
            elem_classes=["chatbot-area"],
        )

        add_feedback_below_chatbot()

        with gr.Row(elem_classes="input-controls-row"):
            user_input = gr.Textbox(
                placeholder="Ask me something...",
                label="Your question:",
                scale=4,
            )

            with gr.Column(elem_classes="right-controls", scale=0):
                copy_btn = gr.Button("📋 Copy Last Response", elem_classes=["wf-btn"])
                actions = add_user_actions(chatbot, retrieve_and_answer)
                retry_btn = actions.get("retry")
                if isinstance(retry_btn, gr.Button):
                    retry_btn.elem_classes = (retry_btn.elem_classes or []) + ["wf-btn"]
                send_btn = gr.Button("Send", elem_classes=["wf-btn"])

        send_btn.click(fn=answer_fn, inputs=[user_input, chatbot], outputs=chatbot)
        user_input.submit(fn=answer_fn, inputs=[user_input, chatbot], outputs=chatbot)

        gr.HTML("""
        <script>
        document.addEventListener("keydown", function (e) {
            const ta = e.target;
            if (!ta || ta.tagName !== "TEXTAREA") return;
            if (e.shiftKey && e.key === "Enter") return;
            if (!e.shiftKey && e.key === "Enter") {
                e.preventDefault(); e.stopPropagation();
                const sendBtn = Array.from(
                    document.querySelectorAll("button")
                ).find(btn => btn.textContent.trim() === "Send");
                if (sendBtn) sendBtn.click();
            }
        });
        </script>
        """)

    return demo
