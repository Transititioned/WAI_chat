# ==========================================================
# app/chatbot.py — WorkFriend WAI (v4.x)
# ==========================================================

import os
from pathlib import Path
import re
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


def _rag_debug_enabled() -> bool:
    return os.getenv("RAG_DEBUG", "").lower() == "true"


def _debug(message: str):
    if _rag_debug_enabled():
        print(f"[RAG_DEBUG] {message}")


def _normalize_text(value: str) -> str:
    value = value or ""
    value = value.lower()
    value = re.sub(r"[_\-]+", " ", value)
    value = re.sub(r"[^a-z0-9\s]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _quoted_phrases(question: str):
    return [
        _normalize_text(match)
        for match in re.findall(r"['\"]([^'\"]+)['\"]", question)
        if _normalize_text(match)
    ]


def _source_key(metadata: dict) -> str:
    return metadata.get("source_path") or metadata.get("source_filename") or metadata.get("source", "")


def _source_chunks(source_key: str, limit: int = 8):
    matches = [
        doc for doc in corpus_docs
        if _source_key(doc["metadata"]) == source_key
    ]
    matches.sort(key=lambda doc: doc["metadata"].get("chunk_index", 0))
    return matches[:limit]


def _metadata_candidates(metadata: dict):
    source = metadata.get("source", "")
    filename = metadata.get("source_filename", source)
    source_stem = Path(filename).stem
    title = metadata.get("title", "")
    heading = metadata.get("heading_path", "")

    return {
        "title": title,
        "filename": filename,
        "source_stem": source_stem,
        "source": source,
        "heading": heading,
    }


def _exact_source_match(question: str):
    query_norm = _normalize_text(question)
    quoted = _quoted_phrases(question)
    best_match = None

    for doc in corpus_docs:
        metadata = doc["metadata"]
        candidates = _metadata_candidates(metadata)

        for match_type, value in candidates.items():
            value_norm = _normalize_text(value)
            if not value_norm or len(value_norm) < 4:
                continue

            is_match = value_norm in query_norm
            is_match = is_match or any(
                phrase == value_norm
                or value_norm.startswith(phrase)
                or phrase in value_norm
                for phrase in quoted
            )

            if not is_match:
                continue

            score = len(value_norm)
            if match_type == "title":
                score += 100
            elif match_type in {"filename", "source_stem", "source"}:
                score += 75
            else:
                score += 40

            if not best_match or score > best_match["score"]:
                best_match = {
                    "score": score,
                    "match_type": match_type,
                    "matched_value": value,
                    "source_key": _source_key(metadata),
                }

    return best_match


def _metadata_matches(question: str, domain: str | None = None, limit: int = 4):
    terms = [term for term in _normalize_text(question).split() if len(term) >= 4]
    phrase = _normalize_text(question)
    scored = []

    for doc in corpus_docs:
        metadata = doc["metadata"]
        if domain and metadata.get("domain") != domain:
            continue

        metadata_text = " ".join([
            metadata.get("title", ""),
            metadata.get("source", ""),
            metadata.get("source_filename", ""),
            metadata.get("source_path", ""),
            metadata.get("heading_path", ""),
            metadata.get("type", ""),
            metadata.get("doc_type", ""),
            metadata.get("domain", ""),
            metadata.get("tags", ""),
            metadata.get("status", ""),
        ]).lower()
        metadata_text = _normalize_text(metadata_text)

        score = 0
        if phrase and phrase in metadata_text:
            score += 25
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
        title = metadata.get("title") or "Untitled"
        heading = metadata.get("heading_path") or "No heading captured"
        confidence = metadata.get("confidence", "unspecified")
        tags = metadata.get("tags") or "none"

        formatted.append(
            f"[Source: {source} | Title: {title} | Domain: {domain} | "
            f"Tags: {tags} | Heading: {heading} | Confidence: {confidence}]\n"
            f"{content}"
        )

    return "\n\n".join(formatted)


def _semantic_search(question: str, domain: str | None = None, k: int = 4):
    filter_arg = {"domain": domain} if domain else None

    try:
        if filter_arg:
            docs_with_scores = vectordb.similarity_search_with_score(question, k=k, filter=filter_arg)
        else:
            docs_with_scores = vectordb.similarity_search_with_score(question, k=k)
        return [doc for doc, _ in docs_with_scores], docs_with_scores
    except Exception as e:
        _debug(f"similarity scores unavailable: {e}")
        if filter_arg:
            return vectordb.similarity_search(question, k=k, filter=filter_arg), []
        return vectordb.similarity_search(question, k=k), []


def _retrieve(question: str, domain: str | None):
    exact = _exact_source_match(question)

    if exact:
        docs = _source_chunks(exact["source_key"])
        matched_title = exact["matched_value"] if exact["match_type"] in {"title", "heading"} else "none"
        matched_filename = exact["matched_value"] if exact["match_type"] in {"filename", "source_stem", "source"} else "none"
        retrieval_mode = "exact filename" if matched_filename != "none" else "exact title"
        _debug(f"selected_domain={domain or 'none'}")
        _debug(f"matched_title={matched_title}")
        _debug(f"matched_filename={matched_filename}")
        _debug(f"retrieval_mode={retrieval_mode}")
        _debug(f"source_files={sorted({_source_key(doc['metadata']) for doc in docs})}")
        _debug(f"chunk_count={len(docs)}")
        return docs

    matches = _metadata_matches(question, domain=domain)

    if domain:
        vector_docs, scores = _semantic_search(question, domain=domain, k=4)
        if len(vector_docs) < 2:
            fallback_docs, fallback_scores = _semantic_search(question, k=4)
            vector_docs.extend(fallback_docs)
            scores.extend(fallback_scores)
    else:
        vector_docs, scores = _semantic_search(question, k=4)

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

    mode = "metadata" if matches else "semantic"
    _debug(f"selected_domain={domain or 'none'}")
    _debug(f"matched_title=none")
    _debug(f"matched_filename=none")
    _debug(f"retrieval_mode={mode}")
    _debug(f"source_files={sorted({_source_key(doc['metadata'] if isinstance(doc, dict) else doc.metadata) for doc in combined})}")
    _debug(f"chunk_count={len(combined)}")
    if scores:
        score_parts = [
            f"{doc.metadata.get('source_path', doc.metadata.get('source', 'unknown'))}:{score}"
            for doc, score in scores
        ]
        _debug(f"similarity_scores={score_parts}")

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
        history = history or []
        reply = retrieve_and_answer(msg)
        history = history + [(msg, reply)]
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
