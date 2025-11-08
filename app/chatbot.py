# ==========================================================
# app/chatbot.py — WorkFriend Chatbot (v2.6 — Final Above-the-Fold Alignment)
# ==========================================================

import gradio as gr
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from pathlib import Path
from app.chatbot_actions import add_user_actions, add_feedback_below_chatbot


def init_chatbot():
    # ... (Setup and LLM functions remain unchanged) ...

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
    # 🎨 Styling — Final Layout Tightening (Minimal changes from v2.5 CSS)
    # ======================================================
    custom_css = """
    /* --- Global Tightening (Highly Aggressive) --- */
    .gradio-container, .block, .wrap, .gradio-app, .svelte-1ipelgc {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin: 0 !important;
        gap: 0 !important;
    }
    /* Hide the Gradio footer */
    footer, .footer, .svelte-1ipelgc > div:last-child {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* --- Chatbot Compact (Set to 275px) --- */
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

    /* --- Feedback Row Adjustments --- */
    /* Target the feedback row to eliminate any vertical margin */
    .feedback-row { 
        margin: 0 !important;
        padding: 0 !important;
        min-height: 40px !important; /* Ensure thumbs up/down is visible */
    }

    /* --- Input Row & Buttons (Keep Uniformity) --- */
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
    /* Add a class to the row holding the input and button column */
    .input-controls-row {
        margin-top: -12px !important; /* Pull up to reduce space after feedback */
        padding: 0 !important;
        align-items: flex-end !important;
        gap: 1rem !important;
    }
    """

    # ======================================================
    # 🚀 Gradio UI — Fixed Layout
    # ======================================================
    theme = gr.themes.Default()
    with gr.Blocks(theme=theme, css=custom_css) as demo:
        gr.Markdown("### 💬 WorkFriend Chatbot")
        
        # 1. Chatbot Area
        chatbot = gr.Chatbot(
            label="WorkFriend Conversation",
            type="messages",
            height=420, # Base height maintained, CSS forces max-height to 275px
            elem_classes=["chatbot-area"]
        )
        
        # 2. Feedback (Make sure this has elem_classes to control spacing in 'add_feedback_below_chatbot')
        # Assuming add_feedback_below_chatbot wraps the content in a container with class 'feedback-row'
        add_feedback_below_chatbot() 

        # 3. Input and Buttons (Horizontal Row for alignment)
        with gr.Row(elem_classes="input-controls-row"):
            # Left: Text Input (Scales to fill space)
            user_input = gr.Textbox(
                placeholder="Ask me something...",
                label="Your question:",
                scale=4,
            )

            # Right: Button Column (Fixed width)
            with gr.Column(elem_classes="right-controls", scale=0): 
                copy_btn = gr.Button("📋 Copy Last Response", elem_classes=["wf-btn"], variant="primary")

                actions = add_user_actions(chatbot, retrieve_and_answer)
                retry_btn = actions.get("retry")
                if isinstance(retry_btn, gr.Button):
                    retry_btn.elem_classes = (retry_btn.elem_classes or []) + ["wf-btn"]

                send_btn = gr.Button("Send", elem_classes=["wf-btn"], variant="primary")

        # --- Event bindings and JS remain unchanged ---
        send_btn.click(fn=answer_fn, inputs=[user_input, chatbot], outputs=chatbot)

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

    return demo