# ==========================================================
# app/chatbot.py — WAI Chatbot (Safe Stable Build)
# ==========================================================

import gradio as gr
import os
from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.router import route, postprocess_answer # <-- works now

from app.chatbot_actions import add_user_actions, add_feedback_below_chatbot


# ==========================================================
# Init + Vector Store
# ==========================================================
def init_chatbot():

    ARTICLES_DIR = Path("content/articles")
    if not ARTICLES_DIR.exists():
        ARTICLES_DIR = Path("content")       # fallback
    INDEX_DIR = Path("index")

    openai_key = os.getenv("OPENAI_API_KEY")
    embedding = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=openai_key)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.28, openai_api_key=openai_key)


    # --- read markdown corpus safely ---
    docs = []
    for md_file in ARTICLES_DIR.glob("*.md"):
        text = md_file.read_text(encoding="utf-8").strip()
        if text:
            chunks = [text[i:i+1500] for i in range(0, len(text), 1500)]
            for chunk in chunks:
                docs.append({"content": chunk, "metadata": {"source": md_file.name}})

    vectordb = Chroma.from_texts(
        texts=[d["content"] for d in docs],
        embedding=embedding,
        metadatas=[d["metadata"] for d in docs]
    )
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})


    # ======================================================
    # Retrieval + Router + Answer
    # ======================================================
    def extract_text(d):
        if hasattr(d, "page_content"): return d.page_content
        if isinstance(d, dict) and "content" in d: return d["content"]
        if isinstance(d, str): return d
        return str(d)

    def retrieve_and_answer(question: str):
        lens_prompt = route(question)
        results = retriever.invoke(question)
        context = "\n\n".join(extract_text(r) for r in results)

        prompt = ChatPromptTemplate.from_template(
            "{lens}\n\nContext:\n{ctx}\n\n"
            "Answer using:\n"
            "1. **Answer** – short & useful\n"
            "2. **Why this matters** – reasoning\n"
            "3. **Example scripts/questions/plays** if relevant\n\n"
            "User Question: {q}"
        ).format(lens=lens_prompt, ctx=context, q=question)

        resp = llm.invoke(prompt)
        return postprocess_answer(resp.content)


    # ======================================================
    # Gradio UI
    # ======================================================
    def answer_fn(message, history):
        try:
            if not isinstance(history, list): history = []
            history.append({"role": "user", "content": message})

            ans = retrieve_and_answer(message)
            history.append({"role": "assistant", "content": ans})

            return history

        except Exception as e:
            return history + [{"role": "assistant", "content": f"⚠️ Error: {e}"}]


    with gr.Blocks() as demo:

        gr.Markdown("### 💬 WorkFriend Chatbot")

        chatbot = gr.Chatbot(label="WorkFriend Conversation", type="messages", height=420)
        add_feedback_below_chatbot()

        user_input = gr.Textbox(label="Your question:", placeholder="Ask something...")
        send_btn  = gr.Button("Send")

        actions = add_user_actions(chatbot, retrieve_and_answer)
        retry_btn = actions.get("retry")

        send_btn.click(answer_fn, inputs=[user_input, chatbot], outputs=chatbot)
        user_input.submit(answer_fn, inputs=[user_input, chatbot], outputs=chatbot)

    return demo
