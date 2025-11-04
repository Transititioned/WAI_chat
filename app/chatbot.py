# ==========================================================
# app/chatbot_actions.py
# ----------------------------------------------------------
# Modular chatbot actions for WorkFriend / CaveBot
# ✅ Retry button aligned with input
# ✅ Large thumbs (green/orange toggle, cross-browser consistent)
# ✅ Clean, minimal UX
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

        # Handle both tuple and dict message formats
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
# Feedback (👍👎) Buttons
# ----------------------------------------------------------
def add_feedback_actions():
    """Adds thumbs-up and thumbs-down with color toggle and consistent sizing."""
    css = """
    <style>
    /* Alignment tweaks */
    textarea, input[type="text"] {
        margin-bottom: 10px !important;
    }

    #retry-button {
        margin-top: 6px !important;
    }

    .feedback-container {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 3rem;
        margin-top: 18px;
    }

    .thumb-btn {
        font-size: 6rem;                     /* Large thumbs */
        line-height: 1;
        width: 100px;                        /* Fixed visual box */
        height: 100px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: none;
        border: none;
        cursor: pointer;
        transition: transform 0.25s ease, filter 0.25s ease;
        user-select: none;
        font-family: "Noto Color Emoji", "Apple Color Emoji", "Segoe UI Emoji", sans-serif;
    }

    .thumb-btn:hover {
        transform: scale(1.15);
        filter: brightness(1.25);
    }

    .thumb-up.active {
        color: #2ECC71 !important;            /* Green */
        text-shadow: 0 0 10px #2ECC71;
    }

    .thumb-down.active {
        color: #FF7F50 !important;            /* Orange */
        text-shadow: 0 0 10px #FF7F50;
    }
    </style>
    """

    html = """
    <div style='text-align:center; opacity:0.85; font-size:1rem;'>Did this help?</div>
    <div class="feedback-container">
        <button class="thumb-btn thumb-up" id="thumbUp">👍</button>
        <button class="thumb-btn thumb-down" id="thumbDown">👎</button>
    </div>

    <script>
    const up = document.getElementById("thumbUp");
    const down = document.getElementById("thumbDown");
    if (up && down) {
        up.onclick = () => {
            up.classList.toggle("active");
            down.classList.remove("active");
        };
        down.onclick = () => {
            down.classList.toggle("active");
            up.classList.remove("active");
        };
    }
    </script>
    """

    return gr.HTML(css + html)


# ----------------------------------------------------------
# Combined Actions Loader
# ----------------------------------------------------------
def add_user_actions(chatbot, retrieve_fn):
    """
    Returns a dict of all active user-interaction buttons:
    Retry + Feedback (👍👎)
    """
    retry_btn = add_retry_action(chatbot, retrieve_fn)
    feedback = add_feedback_actions()

    return {
        "retry": retry_btn,
        "feedback": feedback,
    }
