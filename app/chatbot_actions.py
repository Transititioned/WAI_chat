# ==========================================================
# app/chatbot_actions.py
# ----------------------------------------------------------
# Modular chatbot actions for WorkFriend / CaveBot
# ✅ Retry / Copy / Speak
# ✅ HTML feedback thumbs with working colour toggle
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
# Feedback (👍👎) Buttons — HTML version (fully controllable)
# ----------------------------------------------------------
def add_feedback_actions():
    """Adds thumbs-up and thumbs-down with working colour toggle."""
    css = """
    <style>
    .feedback-container {
        display: flex;
        justify-content: space-around;
        align-items: center;
        gap: 1rem;
        margin-top: 10px;
    }
    .thumb-btn {
        font-size: 1.3rem;
        padding: 8px 20px;
        border-radius: 10px;
        border: 1px solid #ccc;
        background: #eee;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
        user-select: none;
    }
    .thumb-btn:hover {
        transform: scale(1.1);
    }
    .thumb-up.active {
        background-color: #3CB371 !important;  /* Green */
        color: white !important;
        border: none;
    }
    .thumb-down.active {
        background-color: #FF8C00 !important;  /* Orange */
        color: white !important;
        border: none;
    }
    </style>
    """

    html = """
    <div style='text-align:center; opacity:0.75;'>Did this help?</div>
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
