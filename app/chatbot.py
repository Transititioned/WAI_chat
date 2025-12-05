# ==========================================================
# app/chatbot.py — WorkFriend Chatbot (Alpha-safe corpus load)
# ==========================================================

import gradio as gr
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from pathlib import Path
from app.chatbot_actions import add_user_actions, add_feedback_below_chatbot


def init_chatbot():
    # ------------------------------------------------------
    # Paths + Model setup
    # ------------------------------------------------------

    # 🔥 MINIMAL CHANGE: Load multiple content folders
    CORPUS_DIRS = [
        Path("content/articles"),
        Path("content/wai_change_mgmt_library"),
        Path("content/wai_project_mgmt"),
        Path("content/data_mgmt_library"),
    ]

    INDEX_DIR = Path("index")

    openai_key = os.getenv("OPENAI_API_KEY")
    embedding = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=openai_key)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, openai_api_key=openai_key)

    # ------------------------------------------------------
    # Vector store build (minimal edits)
    # ------------------------------------------------------
    docs = []

    # 🔥 MINIMAL CHANGE: Loop through all corpora
    for DIR in CORPUS_DIRS:
        if DIR.exists():
            for md_file in DIR.glob("*.md"):
                text = md_file.read_text(encoding="utf-8").strip()
                if not text:
                    continue
                chunks = [text[i:i + 1500] for i in range(0, len(text), 1500)]
                for chunk in chunks:
                    docs.append({"content": chunk, "metadata": {"source": md_file.name}})

    # Rest unchanged — vectorstore + retriever same behaviour
    vectordb = Chroma.from_texts(
        texts=[d["content"] for d in docs],
        embedding=embedding,
        metadatas=[d["metadata"] for d in docs],
    )
    retriever = vectordb.as_retriever(search_kwargs={"k": 4})  # small improvement, safe

    prompt = ChatPromptTemplate.from_template(
        "Use the following context to answer clearly and concisely:\n\n{context}\n\nQuestion: {question}"
    )

    # ------------------------------------------------------
    # Retrieval + Answer logic
    # ------------------------------------------------------
    def retrieve_and_answer(question: str):
        retrieved_docs = retriever.invoke(question)
        context = "\n\n".join([d.page_content for d in retrieved_docs])
        filled = prompt.format(context=context, question=question)
        response = llm.invoke(filled)
        return response.content

    def answer_fn(message, history):
        try:
            history = history + [{"role": "user", "content": message}]
            answer = retrieve_and_answer(message)
            history = history + [{"role": "assistant", "content": answer}]
            return history
        except Exception as e:
            return history + [{"role": "assistant", "content": f"⚠️ Error: {e}"}]

    # ------------------------------------------------------
    # UI — unchanged below this line
    # ------------------------------------------------------

    custom_css = """
    (KEEP YOUR EXISTING CSS BLOCK HERE — unchanged)
    """

    theme = gr.themes.Default()

    with gr.Blocks(theme=theme, css=custom_css) as demo:
        wakeup_msg = gr.Markdown(
            "### 💤 WAI is waking up…<br>This can take 5–10 seconds if the server was resting.",
            elem_id="wai_wakeup"
        )

        gr.HTML("""<script>/* WAKE-UP PATCH BLOCK — unchanged */</script>""")

        gr.Markdown("### 💬 WorkFriend Chatbot")

        chatbot = gr.Chatbot(
            label="WorkFriend Conversation",
            type="messages",
            height=420,
            elem_classes=["chatbot-area"]
        )

        add_feedback_below_chatbot()

        with gr.Row(elem_classes="input-controls-row"):
            user_input = gr.Textbox(
                placeholder="Ask me something...",
                label="Your question:",
                scale=4
            )

            with gr.Column(elem_classes="right-controls", scale=0):
                copy_btn = gr.Button("📋 Copy Last Response", elem_classes=["wf-btn"], variant="primary")

                # retry + send — unchanged
                actions = add_user_actions(chatbot, retrieve_and_answer)
                retry_btn = actions.get("retry")
                if isinstance(retry_btn, gr.Button):
                    retry_btn.elem_classes = (retry_btn.elem_classes or []) + ["wf-btn"]

                send_btn = gr.Button("Send", elem_classes=["wf-btn"], variant="primary")

        send_btn.click(fn=answer_fn, inputs=[user_input, chatbot], outputs=chatbot)
        user_input.submit(fn=answer_fn, inputs=[user_input, chatbot], outputs=chatbot)

        gr.HTML("""<script>/* ENTER KEY SUBMIT — unchanged */</script>""")

    return demo
