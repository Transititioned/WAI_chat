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


import gradio as gr

# ----------------------------------------------------------
# Retry Action
# ----------------------------------------------------------
def add_retry_action(chatbot, retrieve_fn):
    """Adds a working Retry button that reprocesses the last user message."""
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
# Copy Action
# ----------------------------------------------------------
def add_copy_action(chatbot):
    """
    Adds a Copy button that copies the last assistant message
    to the user's clipboard (client-side JS).
    """
    copy_btn = gr.Button("📋 Copy", variant="secondary")

    copy_btn.click(
        None,
        _js="""
        () => {
            const chatbot = gradioApp().querySelector('gradio-chatbot');
            if (!chatbot) return;
            const messages = chatbot.querySelectorAll('.message');
            if (!messages.length) return alert('No messages yet.');
            // Find last bot message
            const lastBot = Array.from(messages)
                .reverse()
                .find(m => m.classList.contains('bot'));
            if (lastBot) {
                const text = lastBot.innerText || '';
                navigator.clipboard.writeText(text);
            } else {
                alert('No bot message found to copy.');
            }
        }
        """
    )
    return copy_btn


# ----------------------------------------------------------
# Unified Helper
# ----------------------------------------------------------
def add_user_actions(chatbot, retrieve_fn):
    retry_btn = add_retry_action(chatbot, retrieve_fn)
    copy_btn = add_copy_action(chatbot)

    # (Mic or other actions can be added later)
    return {
        "retry": retry_btn,
        "copy": copy_btn,
    }
