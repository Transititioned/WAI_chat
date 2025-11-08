# ==========================================================
# app/chatbot.py — WAI Chatbot Stable Mint Edition
# ==========================================================

import gradio as gr
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from pathlib import Path
from app.chatbot_actions import add_user_actions, add_feedback_below_chatbot


def init_chatbot():
    ARTICLES_DIR = Path("content/articles")
    if not ARTICLES_DIR.exists():
        ARTICLES_DIR = Path(".")
    INDEX_DIR = Path("index")

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

    prompt = ChatPromptTemplate.from_template(
        "Use the following context to answer clearly and concisely:\n\n{context}\n\nQuestion: {question}"
    )

    def retrieve_and_answer(question: str):
        retrieved_docs = retriever.invoke(question)
        context = "\n\n".join([d.page_content for d in retrieved_docs])
        filled_prompt = prompt.format(context=context, question=question)
        response = llm.invoke(filled_prompt)
        return response.content

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
    # ✅ Gradio Blocks UI — Mint Buttons + Equal Sizing
    # ==========================================================
    with gr.Blocks(css="""
        .input-row {
            display: flex;
            align-items: flex-end;
            gap: 1rem;
        }
        .right-controls {
            display: flex;
            flex-direction: column;
            width: 180px;
        }
        .copy-btn, .gr-button {
            background: #00c4b3 !important;  /* mint green */
            color: white !important;
            border: none !important;
            padding: 10px 0 !important;
            border-radius: 6px !important;
            cursor: pointer !important;
            font-size: 0.95rem !important;
            font-weight: 600 !important;
            width: 100% !important;
            height: 44px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 6px !important;
        }
        .copy-btn:hover, .gr-button:hover {
            filter: brightness(1.1);
        }
    """) as demo:
        gr.Markdown("### 💬 WorkFriend Chatbot")

        chatbot = gr.Chatbot(label="WorkFriend Conversation", type="messages")
        add_feedback_below_chatbot()

        with gr.Row(elem_classes="input-row"):
            user_input = gr.Textbox(
                placeholder="Ask me something...",
                label="Your question:",
                scale=4
            )

            with gr.Column(elem_classes="right-controls"):
                gr.HTML(
                    """
                    <button id="copyResponseBtn" class="copy-btn">
                        <span>📋</span> <span>Copy Last Response</span>
                    </button>

                    <script>
                    setTimeout(() => {
                      const btn = document.getElementById("copyResponseBtn");
                      function getLastBotMessage() {
                        const chatEls = document.querySelectorAll('.message.bot, .message.assistant');
                        if (chatEls.length === 0) return '';
                        const lastEl = chatEls[chatEls.length - 1];
                        return lastEl.textContent || '';
                      }
                      if (btn) {
                        btn.addEventListener("click", () => {
                          const content = getLastBotMessage();
                          if (!content) return alert("No chatbot response found yet.");
                          btn.innerHTML = "<span>✅</span> <span>Copied!</span>";
                          navigator.clipboard.writeText(content)
                            .then(() => {
                              setTimeout(() => btn.innerHTML = "<span>📋</span> <span>Copy Last Response</span>", 1500);
                            })
                            .catch(() => alert("Clipboard blocked ⚠️"));
                        });
                      }
                    }, 2000);
                    </script>
                    """
                )

                actions = add_user_actions(chatbot, retrieve_and_answer)
                retry_btn = actions.get("retry")
                send_btn = gr.Button("Send", variant="primary")

        send_btn.click(fn=answer_fn, inputs=[user_input, chatbot], outputs=chatbot)

    return demo
