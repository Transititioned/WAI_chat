# ==========================================================
# app/chatbot_actions.py
# ----------------------------------------------------------
# Modular UX actions for WorkFriend WAI
# Includes:
#  - Feedback thumbs
#  - Retry last message
#  - Copy last response 📋
#  - Spinner hook for send UX
# ==========================================================

import gradio as gr

# ==========================================================
# 👍👎 FEEDBACK BLOCK
# ==========================================================
def add_feedback_below_chatbot():
    """Adds balanced thumbs-up/down SVG buttons below chat window."""
    css = """
    <style>
    .feedback-wrapper { text-align:center; margin-top:10px; }
    .feedback-container {
        display:flex; justify-content:center; align-items:center;
        gap:1.2rem; margin-top:2px;
    }
    .thumb-btn {
        width:32px; height:32px; background:none; border:none; cursor:pointer;
        transition:transform .25s ease, filter .25s ease;
    }
    .thumb-btn svg {
        width:100%; height:100%; fill:#aaa;
        transition:fill .3s ease, filter .3s ease;
    }
    .thumb-btn:hover { transform:scale(1.08); }
    .thumb-up.active svg { fill:#22c55e; filter:drop-shadow(0 0 4px #22c55e); }
    .thumb-down.active svg { fill:#f97316; filter:drop-shadow(0 0 4px #f97316); }
    </style>
    """

    html = """
    <div class="feedback-wrapper">
        <span style='font-size:.85rem;color:#666;margin-right:6px'>Did this help?</span>
        <div class="feedback-container">
            <button class="thumb-btn thumb-up" id="thumbUp"
                onclick="this.classList.toggle('active');
                         document.getElementById('thumbDown').classList.remove('active');">
                <svg viewBox="0 0 24 24"><path d="M1 21h4V9H1v12zM23 10c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32
                c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0
                1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z"/></svg>
            </button>
            <button class="thumb-btn thumb-down" id="thumbDown"
                onclick="this.classList.toggle('active');
                         document.getElementById('thumbUp').classList.remove('active');">
                <svg viewBox="0 0 24 24"><path d="M15 3H6c-.83 0-1.54.5-1.84 1.22L1.14 11.27C1.05 11.5 1
                11.74 1 12v2c0 1.1.9 2 2 2h6.31l-.95 4.57-.03.32c0 .41.17.79.44
                1.06L9.83 23l6.59-6.59c.37-.36.59-.86.59-1.41V5c0-1.1-.9-2-2-2zm4
                0v12h4V3h-4z"/></svg>
            </button>
        </div>
    </div>
    """
    return gr.HTML(css + html)


# ==========================================================
# 🔄 Retry Last Message
# ==========================================================
def add_retry_action(chatbot, retrieve_fn):
    """Re-runs the last user question."""
    def retry_last(history):
        if not history:
            return history

        # get most recent USER message
        last_user = None
        for msg in reversed(history):
            if isinstance(msg, dict) and msg.get("role") == "user":
                last_user = msg["content"]
                break

        if not last_user:
            return history

        try:
            new_answer = retrieve_fn(last_user)
            history.append({"role": "assistant", "content": new_answer})
        except Exception as e:
            history.append({"role": "assistant", "content": f"⚠️ Retry failed: {e}"})
        return history

    btn = gr.Button("Retry Last", variant="secondary")
    btn.click(fn=retry_last, inputs=chatbot, outputs=chatbot)
    return btn


# ==========================================================
# 📋 Copy Last Response — (New)
# ==========================================================
def add_copy_last_action(chatbot):
    """Copies most recent assistant reply to clipboard using JS."""
    btn = gr.Button("📋 Copy Last Response", elem_classes=["wf-btn"], variant="primary")

    copy_js = """
    function copyLast() {
        const msgs = [...document.querySelectorAll(".message, .chat-message")];
        if (!msgs.length) return;

        // search from bottom -> first assistant block
        for (let i = msgs.length - 1; i >= 0; i--) {
            const text = msgs[i].innerText || msgs[i].textContent;
            if (text && !text.startsWith("User") && text.trim().length > 2) {
                navigator.clipboard.writeText(text.trim());
                alert("Copied last response 📋");
                break;
            }
        }
    }
    copyLast();
    """

    btn.click(None, None, None, _js=copy_js)
    return btn


# ==========================================================
# ⏳ Spinner (optional hook - already works in chatbot)
# ==========================================================
def add_spinner_behavior(send_btn):
    """Reveals spinner while LLM is generating (if present)."""
    send_btn.click(
        None, None, None,
        _js="""() => {
            const sp = document.querySelector('.gradio-spinner');
            if (sp) sp.style.display='block';
        }"""
    )
    return send_btn


# ==========================================================
# PUBLIC EXPORT — used in chatbot.py
# ==========================================================
def add_user_actions(chatbot, retrieve_fn):
    return {
        "retry": add_retry_action(chatbot, retrieve_fn),
        "copy":  add_copy_last_action(chatbot)
    }
