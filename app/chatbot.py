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
# Monkey-patch gradio_client bug
# ==========================================================
try:
    import gradio_client.utils as _gcu
    _orig = _gcu._json_schema_to_python_type

    def _safe(schema, defs=None):
        if not isinstance(schema, dict):
            return "any"
        return _orig(schema, defs)

    _gcu._json_schema_to_python_type = _safe
except Exception as e:
    print(f"[chatbot] gradio_client patch failed (non-fatal): {e}")


# ==========================================================
# One-time initialisation
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

    # Proven CSS pattern from CaveBot 0.3.9 lessons:
    # Universal padding/margin/gap reset removes invisible spacing that
    # Gradio injects via .block, .wrap, .svelte-* parent containers —
    # this is what actually causes the below-the-fold issue.
    # Combined with a fixed chatbot height + overflow-y: auto for scrolling.
    custom_css = """
        footer, .footer { display: none !important; }

        /* Universal reset — kills all invisible Gradio padding/gaps */
        .gradio-container *,
        .gradio-container,
        .block,
        .wrap,
        .gradio-app,
        .svelte-1ipelgc {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            gap: 0 !important;
        }

        /* Chatbot fixed height with scroll */
        .chatbot-area {
            max-height: 200px !important;
            overflow-y: auto !important;
        }

        /* Restore some breathing room on the input row */
        .input-row {
            margin-top: 8px !important;
            padding-top: 4px !important;
        }

        /* Brand buttons — nuclear override for all Gradio button variants */
        .wf-btn,
        .wf-btn:not(.hidden),
        div.wf-btn,
        button.wf-btn,
        .block .wf-btn,
        .gradio-container button.wf-btn,
        .gradio-container .wf-btn,
        [class*="svelte"] .wf-btn,
        .wf-btn[class*="svelte"] {
            background: #00C4A7 !important;
            background-color: #00C4A7 !important;
            color: white !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            border: none !important;
            box-shadow: none !important;
            transition: background 0.2s ease-in-out !important;
            min-height: 38px !important;
            line-height: 1.2 !important;
            white-space: normal !important;
        }
        .wf-btn:hover,
        button.wf-btn:hover,
        .gradio-container button.wf-btn:hover {
            background: #00A38A !important;
            background-color: #00A38A !important;
        }
    """

    with gr.Blocks(css=custom_css) as demo:

        gr.Markdown("### 💬 WorkFriend Chatbot")

        chatbot = gr.Chatbot(
            label="WorkFriend Conversation",
            height=200,
            elem_classes=["chatbot-area"],
        )

        with gr.Row(elem_classes=["input-row"], equal_height=True):

            user_input = gr.Textbox(
                placeholder="Ask WAI...",
                label="Your question:",
                lines=1,
                scale=4,
            )

            with gr.Column(scale=1, min_width=160):

                actions = add_user_actions(chatbot, retrieve_and_answer)

                if "retry" in actions:
                    actions["retry"].elem_classes = ["wf-btn"]

                send_btn = gr.Button("Send", elem_classes=["wf-btn"])

        send_btn.click(answer_fn, [user_input, chatbot], [chatbot, user_input])
        user_input.submit(answer_fn, [user_input, chatbot], [chatbot, user_input])

    return demo