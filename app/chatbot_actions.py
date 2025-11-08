# ==========================================================
# app/chatbot_actions.py
# ----------------------------------------------------------
# Modular chatbot actions for WorkFriend / CaveBot
# ✅ Retry button aligned with input
# (Feedback temporarily disabled)
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

        # Handle both tuple and dict formats
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

    retry_btn = gr.Button("Retry Last", variant="secondary", elem_id="retry-button")
    retry_btn.click(fn=retry_last, inputs=chatbot, outputs=chatbot)
    return retry_btn


# ----------------------------------------------------------
# Feedback (👍👎) SVG Buttons – DISABLED FOR TESTING
# ----------------------------------------------------------
# def add_feedback_below_chatbot():
#     """
#     Adds balanced thumbs-up/down SVG buttons with sandbox-safe inline logic.
#     This version is meant to appear directly under the chatbot output.
#     """
#     css = """ ... """
#     html = """ ... """
#     return gr.HTML(css + html)


# ----------------------------------------------------------
# Combined Actions Loader
# ----------------------------------------------------------
def add_user_actions(chatbot, retrieve_fn):
    """
    Returns a dict of all user-interaction buttons.
    Currently includes only Retry (Feedback disabled).
    """
    retry_btn = add_retry_action(chatbot, retrieve_fn)

    # feedback = add_feedback_below_chatbot()  # Disabled for now

    return {
        "retry": retry_btn,
        # "feedback": feedback,
    }
