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

    with gr.Blocks() as demo:

        gr.HTML("""
        <style>
            footer, .footer { display: none !important; }

            /* Responsive chatbot height using viewport units.
               Works at any resolution — chatbot takes 55vh,
               leaving ~45vh for header + input controls. */
            div[data-testid="chatbot"] {
                height: 55vh !important;
                max-height: 55vh !important;
                min-height: 200px !important;
            }

            /* The inner scroll container */
            div[data-testid="chatbot"] > div[role="log"] {
                height: 100% !important;
                max-height: 100% !important;
                overflow-y: auto !important;
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
        // Belt-and-braces: set vh-based height via JS too in case
        // the CSS is overridden by Gradio's inline styles.
        (function() {
            function applyHeight() {
                var chatbot = document.querySelector('div[data-testid="chatbot"]');
                if (chatbot) {
                    var vh55 = Math.round(window.innerHeight * 0.55) + 'px';
                    chatbot.style.setProperty('height', vh55, 'important');
                    chatbot.style.setProperty('max-height', vh55, 'important');
                    var log = chatbot.querySelector('div[role="log"]');
                    if (log) {
                        log.style.setProperty('height', '100%', 'important');
                        log.style.setProperty('max-height', '100%', 'important');
                        log.style.setProperty('overflow-y', 'auto', 'important');
                    }
                } else {
                    setTimeout(applyHeight, 50);
                }
            }
            applyHeight();
            window.addEventListener('resize', applyHeight);
        })();
        </script>
        """)

        gr.Markdown("### 💬 WorkFriend Chatbot")

        chatbot = gr.Chatbot(
            label="WorkFriend Conversation",
            height=500,  # fallback only — CSS/JS overrides this
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