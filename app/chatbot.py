# ==========================================================
# app/chatbot.py — WorkFriend WAI (v4.x)
# ==========================================================

import os
from pathlib import Path
import gradio as gr

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.chatbot_actions import add_user_actions
from app.router import route, postprocess_answer


# ==========================================================
# One-time initialisation (shared by UI + API)
# ==========================================================

ARTICLES_DIR = Path("content/articles")
if not ARTICLES_DIR.exists():
    ARTICLES_DIR = Path(".")

openai_key = os.getenv("OPENAI_API_KEY")

embedding = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=openai_key,
)

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.28,
    openai_api_key=openai_key,
)

docs = []
for md in ARTICLES_DIR.glob("*.md"):
    txt = md.read_text(encoding="utf-8").strip()
    if not txt:
        continue
    for i in range(0, len(txt), 1500):
        docs.append({"content": txt[i:i + 1500], "metadata": {"source": md.name}})

vectordb = Chroma.from_texts(
    texts=[d["content"] for d in docs],
    embedding=embedding,
    metadatas=[d["metadata"] for d in docs],
)

retriever = vectordb.as_retriever(search_kwargs={"k": 3})


def retrieve_and_answer(q: str) -> str:
    lens = route(q)
    docs = retriever.invoke(q)
    context = "\n\n".join(d.page_content for d in docs)

    prompt = ChatPromptTemplate.from_template(
        "{system}\n\nContext:\n{context}\n\n"
        "Respond using:\n"
        "1. **Answer**\n"
        "2. **Why it matters**\n"
        "3. **Plays/Examples**\n\n"
        "User: {q}"
    ).format(system=lens, context=context, q=q)

    res = llm.invoke(prompt)
    return postprocess_answer(res.content)


def handle_message(message: str) -> str:
    return retrieve_and_answer(message)


def init_chatbot():

    def answer_fn(msg, history):
        history = history + [{"role": "user", "content": msg}]
        reply = retrieve_and_answer(msg)
        history = history + [{"role": "assistant", "content": reply}]
        return history, ""

    custom_css = """
    /* Hide Gradio footer chrome */
    footer, .footer { display: none !important; }

    /* Stop Blocks from stretching to full viewport height */
    .gradio-container {
        min-height: unset !important;
        height: auto !important;
    }
    .gradio-container > .main > .wrap {
        min-height: unset !important;
    }

    /* Input row layout */
    .input-controls-row {
        margin-top: 8px !important;
        align-items: flex-end !important;
        gap: 0.75rem !important;
    }

    /* Brand buttons */
    .wf-btn {
        background: #00C4A7 !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        height: 38px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border: none !important;
    }
    .wf-btn:hover {
        background: #00A38A !important;
    }
    """

    # fill_height=False stops Gradio injecting min-height:100vh on the container
    with gr.Blocks(css=custom_css, fill_height=False) as demo:

        gr.Markdown("### 💬 WorkFriend Chatbot")

        # height= on the component is the only reliable way to cap chatbot size —
        # Gradio sets it as an inline style which CSS classes can't override
        chatbot = gr.Chatbot(
            label="WorkFriend Conversation",
            height=320,
            type="messages",
        )

        with gr.Row(elem_classes=["input-controls-row"]):

            user_input = gr.Textbox(
                placeholder="Ask WAI...",
                label="Your question:",
                lines=1,
                scale=4,
            )

            with gr.Column(elem_classes=["right-controls"], scale=0, min_width=160):

                actions = add_user_actions(chatbot, retrieve_and_answer)

                if "retry" in actions:
                    actions["retry"].elem_classes = ["wf-btn"]

                send_btn = gr.Button("Send", elem_classes=["wf-btn"])

        send_btn.click(answer_fn, [user_input, chatbot], [chatbot, user_input])
        user_input.submit(answer_fn, [user_input, chatbot], [chatbot, user_input])

    return demo