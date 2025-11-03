# ==========================================================
# app/chatbot_actions.py
# ----------------------------------------------------------
# Modular chatbot actions for WorkFriend / CaveBot
#   - Floating GPT-style UX buttons (Retry, Copy, Speak)
#   - Compatible with Gradio 4.x
# ==========================================================

import gradio as gr

# ----------------------------------------------------------
# Core Retry Action
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

    retry_btn = gr.Button("Retry Last", visible=False)
    retry_btn.click(fn=retry_last, inputs=chatbot, outputs=chatbot)
    return retry_btn


# ----------------------------------------------------------
# Copy + Speak placeholders
# ----------------------------------------------------------
def add_copy_action(chatbot):
    copy_btn = gr.Button("Copy", visible=False)
    copy_btn.click(fn=lambda h: h, inputs=chatbot, outputs=chatbot)
    return copy_btn


def add_voice_action(chatbot):
    mic_btn = gr.Button("Speak", visible=False)
    mic_btn.click(fn=lambda h: h, inputs=chatbot, outputs=chatbot)
    return mic_btn


# ----------------------------------------------------------
# Combined Floating Actions
# ----------------------------------------------------------
def add_floating_actions(chatbot, retrieve_fn):
    """
    Adds floating overlay controls (Retry, Copy, Speak) to the chatbot UI.
    The buttons are rendered as HTML overlay but wired through hidden
    Gradio button components.
    """
    retry_btn = add_retry_action(chatbot, retrieve_fn)
    copy_btn = add_copy_action(chatbot)
    mic_btn = add_voice_action(chatbot)

    # Overlay HTML for floating GPT-style controls
    overlay = gr.HTML(
        """
        <div style="
            position:absolute;
            bottom:90px;
            right:20px;
            display:flex;
            gap:8px;
            z-index:100;
        ">
            <button id='retry-float' class='gr-button gr-button-secondary' style='padding:4px 6px;' title='Retry'>🔁</button>
            <button id='copy-float' class='gr-button gr-button-secondary' style='padding:4px 6px;' title='Copy'>📋</button>
            <button id='mic-float' class='gr-button gr-button-secondary' style='padding:4px 6px;' title='Speak'>🎤</button>
        </div>
        """
    )

    return {
        "overlay": overlay,
        "retry": retry_btn,
        "copy": copy_btn,
        "mic": mic_btn,
    }
