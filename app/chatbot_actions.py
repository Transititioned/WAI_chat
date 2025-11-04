# ==========================================================
# app/chatbot_actions.py
# ----------------------------------------------------------
# Modular chatbot actions for WorkFriend / CaveBot
# ✅ Retry / Copy / Speak
# ✅ Visual feedback: 👍 green, 👎 orange
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
        last_user = None

        if isinstance(history[-1], tuple):
            last_user, _ = history[-1]
        elif isinstance(history[-1], dict) and history[-1].get("role") == "user":
            last_user = history[-1]["content"]
        else:
            for msg in reversed(history):
                if isinstance(msg, dict) and msg.get("role") == "user":
                    last_user = msg["content"]
                    break

        if not last_user:
            return history

        try:
            new_answer = retrieve_fn(last_user)
            if isinstance(history[-1], dict):
                history.append({"role": "assistant", "content": new_answer})
            else:
                history[-1] = (last_user, new_answer)
        except Exception as e:
            if isinstance(history[-1], dict):
                history.append({"role": "assistant", "content": f"⚠️ Retry failed: {e}"})
            else:
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
# Feedback (👍👎) Buttons with forced colour toggle
# ----------------------------------------------------------
def add_feedback_actions():
    """Adds thumbs-up and thumbs-down buttons with strong colour feedback."""
    with gr.Column():
        gr.Markdown("<div style='text-align:center; opacity:0.75;'>Did this help?</div>")
        like_btn = gr.Button("👍", elem_id="thumb_up_btn", variant="secondary", scale=1)
        dislike_btn = gr.Button("👎", elem_id="thumb_down_btn", variant="secondary", scale=1)

    # internal toggle tracker
    state = {"selected": None}

    def toggle_feedback(choice):
        """Switch CSS classes to simulate on/off colour."""
        if choice == "up":
            state["selected"] = "up"
            return (
                gr.Button.update(elem_classes=["active-thumb-up"]),
                gr.Button.update(elem_classes=[]),
            )
        else:
            state["selected"] = "down"
            return (
                gr.Button.update(elem_classes=[]),
                gr.Button.update(elem_classes=["active-thumb-down"]),
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
