# ==========================================================
# app/chatbot_actions.py
# ----------------------------------------------------------
# Modular chatbot actions for WorkFriend / CaveBot
# ✅ Compatible with current Gradio + LangChain setup
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
# Copy & Voice Actions (Dummy versions for now)
# ----------------------------------------------------------
def add_copy_action(chatbot):
    """Adds a Copy button placeholder for future clipboard support."""
    copy_btn = gr.Button("📋 Copy", variant="secondary")
    # Placeholder: returns history untouched
    copy_btn.click(fn=lambda h: h, inputs=chatbot, outputs=chatbot)
    return copy_btn


def add_voice_action(chatbot):
    """Adds a Voice Input button placeholder for future mic capture."""
    mic_btn = gr.Button("🎤 Speak", variant="secondary")
    # Placeholder: no mic functionality yet
    mic_btn.click(fn=lambda h: h, inputs=chatbot, outputs=chatbot)
    return mic_btn


# ----------------------------------------------------------
# Combined Actions Loader
# ----------------------------------------------------------
def add_user_actions(chatbot, retrieve_fn):
    """
    Returns a dict of user-interaction buttons:
    Retry, Copy, and Voice Input.
    """
    retry_btn = add_retry_action(chatbot, retrieve_fn)
    copy_btn = add_copy_action(chatbot)
    mic_btn = add_voice_action(chatbot)

    return {
        "retry": retry_btn,
        "copy": copy_btn,
        "mic": mic_btn,
    }
