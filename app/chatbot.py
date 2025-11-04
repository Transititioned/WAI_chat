# ==========================================================
# app/chatbot.py
# ----------------------------------------------------------
# Purpose:
#   WorkFriend Chatbot (CaveBot core)
#   - Uses LangChain RAG over Markdown corpus
#   - Modular user actions: Retry, Copy
#   - Lazy import to avoid circular-import errors on Spaces
#   - Safe with Hugging Face + Gradio 4.x
# ==========================================================

import gradio as gr
import importlib        # ✅ lazy import safeguard
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from pathlib import Path


def init_chatbot():
    """Initialize and return the Gradio chatbot interface (stable tuple format)."""
    # --- Paths and setup ---
    ARTICLES_DIR = Path("content/articles")
    if not ARTICLES_DIR.exists():
        ARTICLES_DIR = Path(".")
    INDEX_DIR = Path("index")

    # --- LLM setup ---
    openai_key = os.getenv("OPENAI_API_KEY")
    embedding = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=openai_key)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, openai_api_key=openai_key)

    # --- Build vector store from markdown files ---
    docs = []
    for md_file in ARTICLES_DIR.glob("*.md"):
        text = md_file.read_text(encoding="utf-8").strip()
        if not text:
            continue
        chunks = [text[i:i + 1500] for i in range(0, len(text), 1500)]
        for chunk in chunks:
            docs.append({"content": chunk, "metadata": {"source": md_file.name}})

    vectordb = Chroma.from_texts(
        texts=[d["content"] for d in docs],
        embedding=embedding,
        metadatas=[d["metadata"] for d in docs],
    )
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})

    # --- Prompt template ---
    prompt = ChatPromptTemplate.from_template(
        "Use the following context to answer clearly and concisely:\n\n{context}\n\nQuestion: {question}"
    )

    # --- Retrieval and LLM answer ---
    def retrieve_and_answer(question: str):
        """Search vectorstore and get LLM response."""
        retrieved_docs = retriever.invoke(question)
        context = "\n\n".join([d.page_content for d in retrieved_docs])
        filled_prompt = prompt.format(context=context, question=question)
        response = llm.invoke(filled_prompt)
        return response.content

    # --- Chat handler ---
    def answer_fn(message, history):
        """Handle new user message."""
        try:
            answer = retrieve_and_answer(message)
            history = history + [(message, answer)]  # append new tuple
            return history
        except Exception as e:
            error_msg = f"⚠️ Error: {e}"
            history = history + [(message, error_msg)]
            return history

    # ==========================================================
    # ✅ Gradio Blocks App with Modular Action Buttons
    # ==========================================================
    with gr.Blocks() as demo:
        gr.Markdown("### 💬 WorkFriend Chatbot")

        # Use 'messages' type to avoid tuple deprecation warning
        chatbot = gr.Chatbot(label="WorkFriend Conversation", type="messages")

        with gr.Row():
            user_input = gr.Textbox(
                placeholder="Ask me something...",
                label="Your question:",
                scale=4
            )

            with gr.Column(scale=1, min_width=150):
                send_btn = gr.Button("Send", variant="primary")

                # ✅ Lazy import to prevent circular-import issue
                chatbot_actions = importlib.import_module("app.chatbot_actions")
                actions = chatbot_actions.add_user_actions(chatbot, retrieve_and_answer)
                retry_btn = actions["retry"]
                copy_btn = actions["copy"]
                # mic intentionally omitted

        # --- Event bindings ---
        send_btn.click(fn=answer_fn, inputs=[user_input, chatbot], outputs=chatbot)

    return demo
