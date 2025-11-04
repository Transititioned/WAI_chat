with gr.Row():
    like_btn = gr.Button("👍", variant="secondary")
    dislike_btn = gr.Button("👎", variant="secondary")

def toggle_feedback(choice):
    if choice == "up":
        return gr.Button.update(variant="primary"), gr.Button.update(variant="secondary")
    return gr.Button.update(variant="secondary"), gr.Button.update(variant="primary")

like_btn.click(fn=lambda: toggle_feedback("up"), outputs=[like_btn, dislike_btn])
dislike_btn.click(fn=lambda: toggle_feedback("down"), outputs=[like_btn, dislike_btn])
