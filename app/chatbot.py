# ==========================================================
# app/chatbot.py
# ----------------------------------------------------------
# WorkFriend Chatbot (CaveBot core)
# - LangChain RAG over Markdown corpus
# - Modular user actions: Retry + Feedback
# - HTML thumbs-up/down feedback (green/orange)
# - Inline JS+CSS Toolbox (simple local version)
# ==========================================================

import gradio as gr
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from pathlib import Path
from app.chatbot_actions import add_user_actions


def init_chatbot():
    """Initialize and return the Gradio chatbot interface."""
    # --- Paths and setup ---
    ARTICLES_DIR = Path("content/articles")
    if not ARTICLES_DIR.exists():
        ARTICLES_DIR = Path(".")
    INDEX_DIR = Path("index")

    # --- LLM setup ---
    openai_key = os.getenv("OPENAI_API_KEY")
    embedding = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=openai_key)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, openai_api_key=openai_key)

    # --- Build vector store ---
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

    # --- Retrieval & Answer ---
    def retrieve_and_answer(question: str):
        retrieved_docs = retriever.invoke(question)
        context = "\n\n".join([d.page_content for d in retrieved_docs])
        filled_prompt = prompt.format(context=context, question=question)
        response = llm.invoke(filled_prompt)
        return response.content

    # --- Chat handler ---
    def answer_fn(message, history):
        try:
            history = history + [{"role": "user", "content": message}]
            answer = retrieve_and_answer(message)
            history = history + [{"role": "assistant", "content": answer}]
            return history
        except Exception as e:
            history = history + [{"role": "assistant", "content": f"⚠️ Error: {e}"}]
            return history

    # ==========================================================
    # ✅ Gradio Blocks App
    # ==========================================================
    with gr.Blocks() as demo:
        gr.Markdown("### 💬 WorkFriend Chatbot")

        chatbot = gr.Chatbot(label="WorkFriend Conversation", type="messages")

        with gr.Row():
            user_input = gr.Textbox(
                placeholder="Ask me something...",
                label="Your question:",
                scale=4
            )

            with gr.Column(scale=1, min_width=150):
                send_btn = gr.Button("Send", variant="primary")

                # ✅ Modular actions (only Retry + Feedback now)
                actions = add_user_actions(chatbot, retrieve_and_answer)
                retry_btn = actions["retry"]
                feedback = actions["feedback"]

        # --- Bind send button ---
        send_btn.click(fn=answer_fn, inputs=[user_input, chatbot], outputs=chatbot)

        # ======================================================
        # 💡 Inline WorkFriend JS+CSS Toolbox (local HTML block)
        # ======================================================
        gr.HTML("""
        <hr style='margin:16px 0; border:none; border-top:1px solid #ddd;'>
        <div id="toolbox" style="
            text-align:center;
            background:#fafafa;
            border:1px solid #eee;
            border-radius:10px;
            padding:14px;
            max-width:600px;
            margin:0 auto;
            box-shadow:0 1px 3px rgba(0,0,0,0.05);">
            <h4 style="margin-bottom:8px; color:#333;">🧰 WorkFriend JS + CSS Toolbox</h4>
            <input id="copyText" value="Example snippet from WorkFriend Toolbox"
                   style="width:80%; padding:8px; border-radius:6px; border:1px solid #ccc;">
            <button id="copyBtn"
                style="background:#f97316; color:white; border:none; 
                       padding:8px 14px; border-radius:6px; margin-left:8px;
                       cursor:pointer;">📋 Copy</button>
            <p id="copyMsg" style="color:green; display:none; margin-top:6px;">Copied!</p>
        </div>

        <script>
        const btn = document.getElementById("copyBtn");
        const txt = document.getElementById("copyText");
        const msg = document.getElementById("copyMsg");
        if (btn) {
          btn.addEventListener("click", () => {
            navigator.clipboard.writeText(txt.value).then(() => {
              msg.style.display = "block";
              setTimeout(() => msg.style.display = "none", 1500);
            });
          });
        }
        </script>
        """)

    return demo
