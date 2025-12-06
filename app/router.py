# ==========================================================
# app/chatbot.py — WorkFriend WAI (v4.1 Alpha-Safe)
# Routing + Postprocessing integrated properly
# ==========================================================

import gradio as gr
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from pathlib import Path

from app.chatbot_actions import add_user_actions, add_feedback_below_chatbot
from app.router import route, postprocess_answer   # <— valid now


def init_chatbot():

    # ------------------------------------------------------
    # Paths + Model Setup
    # ------------------------------------------------------
    ARTICLES_DIR = Path("content/articles")
    if not ARTICLES_DIR.exists():
        ARTICLES_DIR = Path(".")
    INDEX_DIR = Path("index")

    openai_key = os.getenv("OPENAI_API_KEY")
    embedding = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=openai_key)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.28, openai_api_key=openai_key)


    # ------------------------------------------------------
    # Build Vectorstore (articles only for alpha release)
    # ------------------------------------------------------
    docs = []
    for md_file in ARTICLES_DIR.glob("*.md"):
        text = md_file.read_text(encoding="utf-8").strip()
        if not text:
            continue
        chunks = [text[i:i+1500] for i in range(0, len(text), 1500)]
        for chunk in chunks:
            docs.append({"content": chunk, "metadata": {"source": md_file.name}})

    vectordb = Chroma.from_texts(
        texts=[d["content"] for d in docs],
        embedding=embedding,
        metadatas=[d["metadata"] for d in docs]
    )
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})


    # ------------------------------------------------------
    # Retrieval + WAI Answer Logic
    # ------------------------------------------------------
    def retrieve_and_answer(question: str):

        system_prompt = route(question)  # currently returns "" safely

        retrieved_docs = retriever.invoke(question)
        context = "\n\n".join([d.page_content for d in retrieved_docs])

        prompt = ChatPromptTemplate.from_template(
            "{system}\n\nContext:\n{context}\n\n"
            "Provide a helpful answer.\n\n"
            "User Question: {question}"
        ).format(system=system_prompt, context=context, question=question)

        response = llm.invoke(prompt)

        # 🔥 now compatible — ONLY model text is passed in
        return postprocess_answer(response.content)


    def answer_fn(message, history):
        try:
            history.append({"role": "user", "content": message})
            answer = retrieve_and_answer(message)
            history.append({"role": "assistant", "content": answer})
            return history
        except Exception as e:
            return history + [{"role": "assistant", "content": f"⚠️ Error: {e}"}]


    # ======================================================
    # UI – (existing mint CSS kept exactly as-is)
    # ======================================================

    custom_css = """<KEEP YOUR ORIGINAL FULL CSS HERE - unchanged>"""

    theme = gr.themes.Default()

    with gr.Blocks(theme=theme, css=custom_css) as demo:

        gr.Markdown("### 💤 WAI is waking up…<br>This can take 5–10 seconds if sleeping.")

        gr.Markdown("### 💬 WorkFriend Chatbot")

        chatbot = gr.Chatbot(label="WorkFriend Conversation", type="messages", height=420)

        add_feedback_below_chatbot()

        with gr.Row():
            user_input = gr.Textbox(placeholder="Ask me something...", label="Your question:", scale=4)
            with gr.Column(scale=0):
                copy_btn = gr.Button("📋 Copy Last Response")
                actions = add_user_actions(chatbot, retrieve_and_answer)
                retry_btn = actions.get("retry")
                send_btn = gr.Button("Send")
        
        send_btn.click(answer_fn, [user_input, chatbot], chatbot)
        user_input.submit(answer_fn, [user_input, chatbot], chatbot)

    return demo
