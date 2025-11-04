# ==========================================================
# app/chatbot_actions.py
# ----------------------------------------------------------
# Modular chatbot actions for WorkFriend / CaveBot
# ✅ Retry button (aligned with input box)
# ✅ HTML feedback thumbs (bigger, colored)
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

    # ✅ Aligned baseline styling
    retry_btn = gr.Button("Retry Last", variant="secondary")
    retry_btn.style(container=True)
    retry_btn.elem_id = "retry-button"

    return retry_btn.click(fn=retry_last, inputs=chatbot, outputs=chatbot)


# ----------------------------------------------------------
# Feedback (👍👎) Buttons — HTML version (bigger + aligned)
# ----------------------------------------------------------
def add_feedback_actions():
    """Adds thumbs-up and thumbs-down with working colour toggle."""
    css = """
    <style>
    #retry-button {
        margin-top: 16px !important;     /* ✅ Aligns with textbox bottom */
    }
    .feedback-container {
        display: flex;
        justify-content: space-around;
        align-items: center;
        gap: 1rem;
        margin-top: 10px;
    }
    .thumb-btn {
        font-size: 2.8rem;               /* ✅ Bigger thumbs */
        padding: 12px 30px;
        border-radius: 16px;
        border: 1px solid #bbb;
        background: #f7f7f7;
        cursor: pointer;
        transition: all 0.25s ease-in-out;
        user-select: none;
    }
    .thumb-btn:hover {
        transform: scale(1.15);
    }
    .thumb-up.active {
        background-color: #2ECC71 !important;  /* Green for Like */
        color: white !important;
        border: none;
    }
    .thumb-down.active {
        background-color: #FF7F50 !important;  /* Orange for Dislike */
        color: white !important;
        border: none;
    }
    </style>
    """

    html = """
    <div style='text-align:center; opacity:0.75; font-size:1rem;'>Did this help?</div>
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
    """Returns dict of all active user-interaction buttons."""
    retry_btn = add_retry_action(chatbot, retrieve_fn)
    feedback = add_feedback_actions()

    return {
        "retry": retry_btn,
        "feedback": feedback,
    }
