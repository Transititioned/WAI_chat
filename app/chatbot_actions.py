# ==========================================================
# app/chatbot_actions.py
# ----------------------------------------------------------
# Modular chatbot actions for WorkFriend / CaveBot
# ✅ Retry button aligned with input
# ✅ SVG thumbs-up / thumbs-down (balanced size, subtle glow)
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
# Feedback (👍👎) SVG Buttons – refined sizing
# ----------------------------------------------------------
def add_feedback_actions():
    """Adds balanced thumbs-up/down SVG buttons with toggle and glow."""
    css = """
    <style>
    #retry-button {
        margin-top: 6px !important;
    }

    .feedback-container {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 2rem;
        margin-top: 16px;
    }

    .thumb-btn {
        width: 55px;
        height: 55px;
        background: none;
        border: none;
        cursor: pointer;
        transition: transform 0.25s ease, filter 0.25s ease;
    }

    .thumb-btn svg {
        width: 100%;
        height: 100%;
        fill: #aaa;
        transition: fill 0.3s ease, filter 0.3s ease;
    }

    .thumb-btn:hover {
        transform: scale(1.1);
    }

    .thumb-up.active svg {
        fill: #2ECC71; /* Green */
        filter: drop-shadow(0 0 5px #2ECC71);
    }

    .thumb-down.active svg {
        fill: #FF7F50; /* Orange */
        filter: drop-shadow(0 0 5px #FF7F50);
    }
    </style>
    """

    html = """
    <div style='text-align:center; opacity:0.85; font-size:1rem;'>Did this help?</div>
    <div class="feedback-container">
        <button class="thumb-btn thumb-up" id="thumbUp" title="Helpful">
            <svg viewBox="0 0 24 24">
                <path d="M1 21h4V9H1v12zM23 10c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32
                c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0
                1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z"/>
            </svg>
        </button>
        <button class="thumb-btn thumb-down" id="thumbDown" title="Not helpful">
            <svg viewBox="0 0 24 24">
                <path d="M15 3H6c-.83 0-1.54.5-1.84 1.22L1.14 11.27C1.05 11.5 1
                11.74 1 12v2c0 1.1.9 2 2 2h6.31l-.95 4.57-.03.32c0 .41.17.79.44
                1.06L9.83 23l6.59-6.59c.37-.36.59-.86.59-1.41V5c0-1.1-.9-2-2-2zm4
                0v12h4V3h-4z"/>
            </svg>
        </button>
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
    Returns a dict of all user-interaction buttons:
    Retry + Feedback (👍👎)
    """
    retry_btn = add_retry_action(chatbot, retrieve_fn)
    feedback = add_feedback_actions()

    return {
        "retry": retry_btn,
        "feedback": feedback,
    }
