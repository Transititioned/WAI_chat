# ==========================================================
# app/chatbot_actions.py
# ----------------------------------------------------------
# Modular chatbot actions for WorkFriend / CaveBot
# ✅ Retry button aligned with input
# ✅ Huge thumbs (green/orange), equal size both
# ==========================================================

import gradio as gr

def add_retry_action(chatbot, retrieve_fn):
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

    retry_btn = gr.Button("Retry Last", variant="secondary", elem_id="retry-button")
    retry_btn.click(fn=retry_last, inputs=chatbot, outputs=chatbot)
    return retry_btn

def add_feedback_actions():
    css = """
    <style>
    /* Lower the textbox a bit so alignment is better */
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
        gap: 2.5rem;
        margin-top: 16px;
    }

    .thumb-btn {
        font-size: 4.5rem;                /* Much larger thumbs */
        width: 80px;
        height: 80px;
        padding: 0;
        border-radius: 50%;
        border: 2px solid #bbb;
        background: #f5f5f5;
        cursor: pointer;
        transition: all 0.25s ease-in-out;
        user-select: none;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .thumb-btn:hover {
        transform: scale(1.25);
    }

    .thumb-up.active {
        background-color: #28a745 !important;  /* Green */
        color: white !important;
        border: 2px solid #1e7e34;
    }

    .thumb-down.active {
        background-color: #ff8c00 !important;  /* Orange */
        color: white !important;
        border: 2px solid #cc7000;
    }
    </style>
    """

    html = """
    <div style='text-align:center; opacity:0.8; font-size:1rem;'>Did this help?</div>
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

def add_user_actions(chatbot, retrieve_fn):
    retry_btn = add_retry_action(chatbot, retrieve_fn)
    feedback = add_feedback_actions()
    return {
        "retry": retry_btn,
        "feedback": feedback,
    }
