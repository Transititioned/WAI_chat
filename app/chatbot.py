# ==========================================================
# app/chatbot_actions.py
# ----------------------------------------------------------
# Modular chatbot actions for WorkFriend / CaveBot
# ✅ Compatible with current Gradio + LangChain setup
# ✅ Adds visual thumbs-up / thumbs-down feedback toggle
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
# Copy Action (placeholder)
# ----------------------------------------------------------
def add_copy_action(chatbot):
    """Adds a Copy button placeholder for clipboard copy."""
    copy_btn = gr.Button("📋 Copy", variant="secondary")
    copy_btn.click(fn=lambda h: h, inputs=chatbot, outputs=chatbot)
    return copy_btn


# ----------------------------------------------------------
# Voice Input (placeholder)
# ----------------------------------------------------------
def add_voice_action(chatbot):
    """Adds a Voice Input button placeholder for mic capture."""
    mic_btn = gr.Button("🎤 Speak", variant="secondary")
    mic_btn.click(fn=lambda h: h, inputs=chatbot, outputs=chatbot)
    return mic_btn


# ----------------------------------------------------------
# Feedback (👍👎) Buttons
# ----------------------------------------------------------
def add_feedback_actions():
    """Adds thumbs-up and thumbs-down buttons with simple toggle visual."""
    with gr.Row(equal_height=True):
        gr.Markdown("<div style='text-align:center; opacity:0.75;'>Did this help?</div>")

    with gr.Row(equal_height=True):
        like_btn = gr.Button("👍", variant="secondary", scale=1)
        dislike_btn = gr.Button("👎", variant="secondary", scale=1)

    def toggle_feedback(choice):
        """Switch button variants to simulate selection."""
        if choice == "up":
            return (
                gr.Button.update(variant="primary"),
                gr.Button.update(variant="secondary")
            )
        else:
            return (
                gr.Button.update(variant="secondary"),
                gr.Button.update(variant="primary")
            )

    like_btn.click(fn=lambda: toggle_feedback("up"), outputs=[like_btn, dislike_btn])
    dislike_btn.click(fn=lambda: toggle_feedback("down"), outputs=[like_btn, dislike_btn])

    return {"like": like_btn, "dislike": dislike_btn}


# ----------------------------------------------------------
# Combined Actions Loader
# ----------------------------------------------------------
def add_user_actions(chatbot, retrieve_fn):
    """
    Returns a dict of all user-interaction buttons:
    Retry, Copy, Mic, and Feedback (👍👎).
    """
    retry_btn = add_retry_action(chatbot, retrieve_fn)
    copy_btn = add_copy_action(chatbot)
    mic_btn = add_voice_action(chatbot)
    feedback = add_feedback_actions()

    return {
        "retry": retry_btn,
        "copy": copy_btn,
        "mic": mic_btn,
        "feedback": feedback,
    }
