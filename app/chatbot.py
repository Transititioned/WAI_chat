# ==========================================================
# app/chatbot.py — WorkFriend WAI (v4.x)
# ==========================================================

import os
from pathlib import Path
import gradio as gr

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app import loaders
from app.chatbot_actions import add_user_actions
from app.router import route_info, postprocess_answer


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

CONTENT_DIR = Path("content")
if not CONTENT_DIR.exists():
    CONTENT_DIR = Path(".")

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

corpus_docs = loaders.load_corpus_chunks(CONTENT_DIR)

vectordb = Chroma.from_texts(
    texts=[d["content"] for d in corpus_docs],
    embedding=embedding,
    metadatas=[d["metadata"] for d in corpus_docs],
)


def _keyword_matches(question: str, domain: str | None = None, limit: int = 3):
    terms = [term for term in question.lower().replace("_", " ").split() if len(term) >= 4]
    phrase = question.lower().strip()
    scored = []

    for doc in corpus_docs:
        metadata = doc["metadata"]
        if domain and metadata.get("domain") != domain:
            continue

        metadata_text = " ".join([
            metadata.get("source", ""),
            metadata.get("source_path", ""),
            metadata.get("heading_path", ""),
            metadata.get("doc_type", ""),
            metadata.get("domain", ""),
        ]).lower()

        score = 0
        if phrase and phrase in metadata_text:
            score += 10
        score += sum(1 for term in terms if term in metadata_text)

        if score:
            scored.append((score, doc))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [doc for _, doc in scored[:limit]]


def _metadata_key(doc) -> tuple:
    metadata = doc["metadata"] if isinstance(doc, dict) else doc.metadata
    return metadata.get("source_path"), metadata.get("chunk_index")


def _format_context(docs) -> str:
    formatted = []
    for doc in docs:
        if isinstance(doc, dict):
            content = doc["content"]
            metadata = doc["metadata"]
        else:
            content = doc.page_content
            metadata = doc.metadata

        source = metadata.get("source_path") or metadata.get("source", "unknown source")
        domain = metadata.get("domain", "unknown")
        heading = metadata.get("heading_path") or "No heading captured"
        confidence = metadata.get("confidence", "unspecified")

        formatted.append(
            f"[Source: {source} | Domain: {domain} | Heading: {heading} | Confidence: {confidence}]\n"
            f"{content}"
        )

    return "\n\n".join(formatted)


def _retrieve(question: str, domain: str | None):
    matches = _keyword_matches(question, domain=domain)

    if domain:
        vector_docs = vectordb.similarity_search(
            question,
            k=4,
            filter={"domain": domain},
        )
        if len(vector_docs) < 2:
            vector_docs.extend(vectordb.similarity_search(question, k=4))
    else:
        vector_docs = vectordb.similarity_search(question, k=4)

    combined = []
    seen = set()
    for doc in matches + vector_docs:
        key = _metadata_key(doc)
        if key in seen:
            continue
        seen.add(key)
        combined.append(doc)
        if len(combined) == 5:
            break

    return combined


def retrieve_and_answer(q: str) -> str:
    routing = route_info(q)
    docs = _retrieve(q, routing["domain"])
    context = _format_context(docs)

    prompt = ChatPromptTemplate.from_template(
        "{system}\n\nContext:\n{context}\n\n"
        "Use the provided source labels when grounding the answer. "
        "Distinguish confirmed facts from inferences or assumptions when the context is thin.\n\n"
        "Respond using:\n"
        "1. **Answer**\n"
        "2. **Why it matters**\n"
        "3. **Plays/Examples**\n\n"
        "User: {q}"
    ).format(system=routing["lens"], context=context, q=q)

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
            border: 1.5px solid rgba(0,0,0,0.12) !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.10) !important;
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
