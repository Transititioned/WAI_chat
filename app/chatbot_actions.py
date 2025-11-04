# ==========================================================
# app/chatbot_actions.py
# ----------------------------------------------------------
# Modular chatbot actions for WorkFriend / CaveBot
# ✅ Compatible with current Gradio + LangChain setup
# ✅ Hugging Face Spaces safe (no _js argument)
# ==========================================================

import gradio as gr


# ----------------------------------------------------------
# Retry Last Action
# ----------------------------------------------------------
def add_retry_action(chatbot, retrieve_fn):
    """Adds a Retry Last button that re-runs the last user message."""
    def retry_last(history):
        if not history:
            return history
        last_user, _ = history[-1]
        try:
            new_answer = retrieve_fn(last_user)
            history[-1] = (last_user, new_answer)
        except Exception as e:
            history[-1] = (last_user, f"⚠️ Retry failed: {e}")
        return history

    retry_btn = gr.Button("Retry Last", variant="secondary")
    retry_btn.click(fn=retry_last, inputs=chatbot, outputs=chatbot)
    return retry_btn


# ----------------------------------------------------------
# Copy Action (Spaces-safe version)
# ----------------------------------------------------------
def add_copy_action(chatbot):
    """
    Adds a Copy button that reveals the last assistant message
    in a read-only textbox for manual copy (sandbox-safe).
    """
    copy_btn = gr.Button("📋 Copy", variant="secondary")
    copy_box = gr.Textbox(label="Copied text", visible=False, interactive=False)

    def extract_last(history):
        """Extracts last assistant message for manual copy."""
        if not history:
            return gr.update(value="No messages yet.", visible=True)
        last_user, last_bot = history[-1]
        if not last_bot:
            return gr.update(value="No assistant message yet.", visible=True)
        return gr.update(value=last_bot, visible=True)

    copy_btn.click(fn=extract_last, inputs=chatbot, outputs=copy_box)
    return copy_btn, copy_box


# ----------------------------------------------------------
# Voice Input Placeholder
# ----------------------------------------------------------
def add_voice_action(chatbot):
    """Adds a Voice Input button placeholder for future mic capture."""
    mic_btn = gr.Button("🎤 Speak", variant="secondary")
    mic_btn.click(fn=lambda h: h, inputs=chatbot, outputs=chatbot)
    return mic_btn


# ----------------------------------------------------------
# Combined Actions Loader
# ----------------------------------------------------------
def add_user_actions(chatbot, retrieve_fn):
    """
    Returns a dict of user-interaction buttons and UI elements:
    Retry, Copy (with copy_box), and Voice Input.
    """
    retry_btn = add_retry_action(chatbot, retrieve_fn)
    copy_btn, copy_box = add_copy_action(chatbot)
    mic_btn = add_voice_action(chatbot)

    return {
        "retry": retry_btn,
        "copy": copy_btn,
        "copy_box": copy_box,
        "mic": mic_btn,
    }
