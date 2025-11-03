# ==========================================================
# app/chatbot_actions.py
# ----------------------------------------------------------
# Modular chatbot actions for WorkFriend / CaveBot
# ✅ Gradio 4.x compatible (no _js regression)
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

    retry_btn = gr.Button("🔁 Retry Last", variant="secondary")
    retry_btn.click(fn=retry_last, inputs=chatbot, outputs=chatbot)
    return retry_btn


# ----------------------------------------------------------
# Copy Action (Gradio 4.x safe placeholder)
# ----------------------------------------------------------
def add_copy_action(chatbot):
    """
    Adds a Copy button placeholder.
    Future enhancement: copy last assistant message via JS or Gradio HTML block.
    """
    def fake_copy(history):
        if not history:
            return history + [("📋 Copy", "⚠️ Nothing to copy yet.")]
        last_user, last_bot = history[-1] if history else ("", "")
        confirm_msg = f"✅ Copied last response (simulated): {last_bot[:60]}..."
        return history + [("📋 Copy", confirm_msg)]

    copy_btn = gr.Button("📋 Copy", variant="secondary")
    copy_btn.click(fn=fake_copy, inputs=chatbot, outputs=chatbot)
    return copy_btn


# ----------------------------------------------------------
# Unified Action Loader
# ----------------------------------------------------------
def add_user_actions(chatbot, retrieve_fn):
    """
    Return dictionary of action buttons for modular inclusion.
    Currently supports Retry + Copy.
    """
    retry_btn = add_retry_action(chatbot, retrieve_fn)
    copy_btn = add_copy_action(chatbot)

    return {
        "retry": retry_btn,
        "copy": copy_btn,
    }
