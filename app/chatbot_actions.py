# ==========================================================
# app/chatbot.py
# ----------------------------------------------------------
# Chatbot UI with corrected alignment for input and buttons
# ==========================================================

import gradio as gr
from app.chatbot_actions import add_user_actions
from app.engine import retrieve_answer


def init_chatbot():
    """Initialize the Gradio chatbot interface (aligned input & buttons)."""

    # --- Global CSS overrides ---
    css = """
    <style>
    /* Fix input + button alignment */
    .gradio-container .message-row,
    .gradio-container .input-group {
        display: flex;
        align-items: stretch;
        gap: 0.75rem;
    }

    /* Make sure the textbox and buttons share same baseline */
    textarea.svelte-1ipelgc {
        min-height: 60px !important;
        resize: vertical !important;
        line-height: 1.4em;
    }

    button.primary,
    button.secondary {
        height: auto !important;
        align-self: stretch !important;
        display: flex;
        justify-content: center;
        align-items: center;
        font-weight: 600;
        border-radius: 6px;
    }

    /* Align Retry below Send perfectly */
    #retry-button {
        margin-top: 6px;
    }

    /* Container spacing for the whole interaction area */
    .feedback-container {
        margin-bottom: 24px;
    }
    </style>
    """

    # --- Define chatbot block ---
    with gr.Blocks(css=css, title="WorkFriend Chatbot") as demo:
        gr.Markdown("### 💬 WorkFriend Assistant")

        chatbot = gr.Chatbot(height=400, show_copy_button=True)

        # Input area
        with gr.Row():
            msg = gr.Textbox(
                label="Your question:",
                placeholder="Type your question here...",
                scale=6,
            )
            with gr.Column(scale=1, min_width=150):
                send_btn = gr.Button("Send", variant="primary")
                user_actions = add_user_actions(chatbot, retrieve_answer)
                retry_btn = user_actions["retry"]

        # Feedback (👍👎)
        user_actions["feedback"]

        # --- Chat logic ---
        def respond(user_message, chat_history):
            if not user_message:
                return "", chat_history
            try:
                bot_reply = retrieve_answer(user_message)
            except Exception as e:
                bot_reply = f"⚠️ Error: {e}"
            chat_history.append((user_message, bot_reply))
            return "", chat_history

        send_btn.click(respond, inputs=[msg, chatbot], outputs=[msg, chatbot])
        msg.submit(respond, inputs=[msg, chatbot], outputs=[msg, chatbot])

    return demo


if __name__ == "__main__":
    demo = init_chatbot()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
