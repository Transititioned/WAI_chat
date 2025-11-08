# ==========================================================
# app/chatbot_actions.py
# ----------------------------------------------------------
# Modular chatbot actions for WorkFriend / CaveBot
# ✅ Retry button aligned with input
# ✅ Compact feedback (not returned via user_actions)
# ✅ Sandbox-safe inline event handling
# ==========================================================

import gradio as gr


# ----------------------------------------------------------
# Feedback (👍👎) SVG Buttons – compact inline style
# ----------------------------------------------------------
def add_feedback_below_chatbot():
    """Adds compact thumbs-up/down feedback with text beside icons."""
    css = """
    <style>
    .feedback-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 10px;
        margin-top: 6px;
        color: #555;
        font-size: 0.85rem;
    }
    .thumb-btn {
        width: 22px;
        height: 22px;
        background: none;
        border: none;
        cursor: pointer;
        padding: 0;
        transition: transform 0.2s ease, filter 0.2s ease;
    }
    .thumb-btn svg {
        width: 100%;
        height: 100%;
        fill: #bbb;
        transition: fill 0.2s ease, filter 0.2s ease;
    }
    .thumb-btn:hover svg {
        fill: #777;
    }
    .thumb-btn:hover {
        transform: scale(1.1);
    }
    .thumb-up.active svg {
        fill: #22c55e;
        filter: drop-shadow(0 0 3px #22c55e);
    }
    .thumb-down.active svg {
        fill: #f97316;
        filter: drop-shadow(0 0 3px #f97316);
    }
    </style>
    """

    html = """
    <div class="feedback-wrapper">
        <span>Did this help?</span>
        <button class="thumb-btn thumb-up" id="thumbUp" title="Helpful"
            onclick="this.classList.toggle('active');
                     document.getElementById('thumbDown').classList.remove('active');">
            <svg viewBox="0 0 24 24">
                <path d="M1 21h4V9H1v12zM23 10c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32
                c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0
                1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z"/>
            </svg>
        </button>
        <button class="thumb-btn thumb-down" id="thumbDown" title="Not helpful"
            onclick="this.classList.toggle('active');
                     document.getElementById('thumbUp').classList.remove('active');">
            <svg viewBox="0 0 24 24">
                <path d="M15 3H6c-.83 0-1.54.5-1.84 1.22L1.14 11.27C1.05 11.5 1
                11.74 1 12v2c0 1.1.9 2 2 2h6.31l-.95 4.57-.03.32c0 .41.17.79.44
                1.06L9.83 23l6.59-6.59c.37-.36.59-.86.59-1.41V5c0-1.1-.9-2-2-2zm4
                0v12h4V3h-4z"/>
            </svg>
        </button>
    </div>
    """
    return gr.HTML(css + html)


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
            err = f"⚠️ Retry failed: {e}"
            if isinstance(history[-1], dict):
                history.append({"role": "assistant", "content": err})
            else:
                history[-1] = (last_user, err)
        return history

    retry_btn = gr.Button("Retry Last", variant="secondary")
    retry_btn.click(fn=retry_last, inputs=chatbot, outputs=chatbot)
    return retry_btn


# ----------------------------------------------------------
# Combined Actions Loader (Retry only)
# ----------------------------------------------------------
def add_user_actions(chatbot, retrieve_fn):
    """Returns user-interaction controls (Retry only)."""
    retry_btn = add_retry_action(chatbot, retrieve_fn)
    return {"retry": retry_btn}
