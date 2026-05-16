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
# Monkey-patch gradio_client bug: "argument of type 'bool' is not iterable"
# Root cause: get_type() in gradio_client/utils.py does `if "const" in schema`
# but schema can be a bool (True/False) when additionalProperties=True/False.
# Fix: guard against non-dict schema before the `in` check.
# ==========================================================
try:
    import gradio_client.utils as _gcu

    _original_get_type = _gcu.get_type

    def _safe_get_type(schema):
        if not isinstance(schema, dict):
            return "any"
        return _original_get_type(schema)

    _gcu.get_type = _safe_get_type
    print("[chatbot] gradio_client.utils.get_type patched OK")
except Exception as e:
    print(f"[chatbot] gradio_client patch failed (non-fatal): {e}")


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

    with gr.Blocks() as demo:

        gr.HTML("""
        <style>
            footer, .footer { display: none !important; }

            /* Stop the gradio-app web component from flex-growing to 100vh */
            gradio-app {
                flex-grow: 0 !important;
                height: auto !important;
                min-height: unset !important;
            }

            .gradio-container,
            .gradio-container > .main,
            .gradio-container > .main > .wrap {
                min-height: unset !important;
                height: auto !important;
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
            .wf-btn:hover { background: #00A38A !important; }
        </style>

        <script>
        // Override flex-grow on gradio-app which is set as an inline style
        // by the page HTML and therefore beats CSS rules.
        (function fix() {
            var app = document.querySelector('gradio-app');
            if (app) {
                app.style.flexGrow = '0';
                app.style.height = 'auto';
                app.style.minHeight = 'unset';
            } else {
                setTimeout(fix, 50);
            }
        })();
        </script>
        """)

        gr.Markdown("### 💬 WorkFriend Chatbot")

        chatbot = gr.Chatbot(
            label="WorkFriend Conversation",
            height=320,
        )

        with gr.Row():
            user_input = gr.Textbox(
                placeholder="Ask WAI...",
                label="Your question:",
                lines=1,
                scale=4,
            )

            with gr.Column(scale=0, min_width=160):

                actions = add_user_actions(chatbot, retrieve_and_answer)

                if "retry" in actions:
                    actions["retry"].elem_classes = ["wf-btn"]

                send_btn = gr.Button("Send", elem_classes=["wf-btn"])

        send_btn.click(answer_fn, [user_input, chatbot], [chatbot, user_input])
        user_input.submit(answer_fn, [user_input, chatbot], [chatbot, user_input])

    return demo