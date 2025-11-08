# ==========================================================
# app/chatbot.py — WorkFriend Chatbot (v1.7 — Compact Uniform Buttons)
# ==========================================================

import gradio as gr
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from pathlib import Path
from app.chatbot_actions import add_user_actions, add_feedback_below_chatbot


def init_chatbot():
    ARTICLES_DIR = Path("content/articles")
    if not ARTICLES_DIR.exists():
        ARTICLES_DIR = Path(".")
    INDEX_DIR = Path("index")

    openai_key = os.getenv("OPENAI_API_KEY")
    embedding = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=openai_key)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, openai_api_key=openai_key)

    # ... (Vector store and prompt setup remains the same) ...
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
    # 🎨 Uniform Button Styling (Simplified for stability)
    # ------------------------------------------------------
    custom_css = """
    /* --- Level 1: Target the Gradio component container (.wf-btn) --- */
    /* Strips padding/margin on the Gradio component wrapper */
    .wf-btn {
        padding: 0 !important; 
        margin: 0 !important;
        min-height: 38px !important;
        height: 38px !important; 
    }

    /* --- Level 2: Target the actual HTML button elements --- */
    .wf-btn button,
    #copyResponseBtn { /* Simplified selector for the HTML button */
        background-color: #00C4A7 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        
        /* CRITICAL: Force Uniform Height */
        height: 38px !important; 
        min-height: 38px !important;
        
        width: 100% !important;
        padding: 6px 0 !important;
        text-align: center !important;
        cursor: pointer !important;
        transition: all 0.2s ease-in-out !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 6px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1) !important;
        margin: 0 !important; 
        line-height: 1 !important;
    }

    .wf-btn button:hover,
    #copyResponseBtn:hover {
        background-color: #00A38A !important;
        transform: translateY(-1px);
    }
    
    /* --- Level 3: Target Gradio's Internal Wrapper Divs to reset space --- */
    .wf-btn > div, 
    .wf-btn > div > div {
        padding: 0 !important; 
        margin: 0 !important;
        min-height: 38px !important;
        height: 38px !important;
    }
    
    /* Nuke Gradio primary/variant overrides */
    .gr-button-primary.wf-btn button, 
    .gr-button-secondary.wf-btn button {
        background-image: none !important;
        box-shadow: none !important;
        background-color: #00C4A7 !important; 
    }

    /* Column/Row Layout */
    .right-controls {
        display: flex !important;
        flex-direction: column !important;
        gap: 8px !important;
        width: 180px !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    .input-row {
        display: flex !important;
        align-items: flex-end !important;
        gap: 1rem !important;
    }
    """

    theme = gr.themes.Default()

    with gr.Blocks(theme=theme, css=custom_css) as demo:
        gr.Markdown("### 💬 WorkFriend Chatbot")

        chatbot = gr.Chatbot(label="WorkFriend Conversation", type="messages", height=420)
        add_feedback_below_chatbot()

        # Define an output component to temporarily hold the last bot message
        last_response = gr.State(value="") 

        with gr.Row(elem_classes="input-row"):
            user_input = gr.Textbox(
                placeholder="Ask me something...",
                label="Your question:",
                scale=4,
            )

            with gr.Column(elem_classes="right-controls"):
                # Copy button: Now pure HTML without JS
                copy_btn = gr.HTML(
                    """
                    <button id="copyResponseBtn" class="wf-btn">
                        <span>📋</span> <span>Copy Last Response</span>
                    </button>
                    """
                )
                
                # We use gr.Row here to ensure these two Gradio components are treated equally
                with gr.Row(elem_classes=["wf-btn-row"], equal_height=True): 
                    # Retry and Send buttons
                    actions = add_user_actions(chatbot, retrieve_and_answer)
                    retry_btn = actions.get("retry")
                    
                    if isinstance(retry_btn, gr.Button):
                        # Apply the class to the Gradio button *component*
                        retry_btn.elem_classes = (retry_btn.elem_classes or []) + ["wf-btn"]

                    send_btn = gr.Button("Send", elem_classes=["wf-btn"], variant="primary")
                
        # --- Functionality Wiring (No custom JS) ---

        def get_last_response(history):
            """Extracts and returns the content of the last assistant message."""
            if history and history[-1]['role'] == 'assistant':
                # Return the message content for the clipboard
                return history[-1]['content']
            return "" # Return empty string if no message or not assistant's

        # 1. Update the state and chatbot on send
        send_btn.click(
            fn=answer_fn, 
            inputs=[user_input, chatbot], 
            outputs=chatbot
        ).then(
            # Extract the last response to the state component
            fn=get_last_response, 
            inputs=chatbot, 
            outputs=last_response
        )
        
        # 2. Wire the copy button to the Gradio clipboard function
        # We must use JS here, but it's the official Gradio/client-side JS API, not embedded script.
        copy_btn.click(
            None, 
            inputs=[last_response], 
            outputs=None, 
            # Use Gradio's built-in clipboard function
            # This is generally allowed/whitelisted even in restricted environments
            js="(last_response) => { navigator.clipboard.writeText(last_response); return ''; }"
        )
        
        # Ensure Retry button also has the wf-btn class (already done above, but good practice)
        if isinstance(retry_btn, gr.Button):
            retry_btn.elem_classes = (retry_btn.elem_classes or []) + ["wf-btn"]
            retry_btn.click(
                fn=get_last_response, 
                inputs=chatbot, 
                outputs=last_response # Update the state on retry as well
            )

    return demo