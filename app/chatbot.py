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
from app.retrieval_policy import (
    detect_retrieval_intent,
    metadata_for,
    metadata_key,
    normalize_text,
    rank_retrieval_candidates,
    source_key,
)
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
    return normalize_text(value)


def _quoted_phrases(question: str):
    return [
        _normalize_text(match)
        for match in re.findall(r"['\"]([^'\"]+)['\"]", question)
        if _normalize_text(match)
    ]


def _source_key(metadata: dict) -> str:
    return source_key(metadata)


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
            metadata.get("secondary_domains", ""),
            metadata.get("stage", ""),
            metadata.get("trigger_phrases", ""),
            metadata.get("retrieval_intent", ""),
            metadata.get("id", ""),
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
    return metadata_key(doc)


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
        doc_type = metadata.get("type") or metadata.get("doc_type") or "unknown"
        heading = metadata.get("heading_path") or "No heading captured"
        confidence = metadata.get("confidence", "unspecified")
        tags = metadata.get("tags") or "none"

        formatted.append(
            f"[Source: {source} | Title: {title} | Type: {doc_type} | Domain: {domain} | "
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


def _semantic_candidates(question: str, domain: str | None = None, k: int = 6):
    docs, scores = _semantic_search(question, domain=domain, k=k)
    score_by_key = {
        _metadata_key(doc): score
        for doc, score in scores
    }
    candidates = []

    for doc in docs:
        distance = score_by_key.get(_metadata_key(doc))
        rank_score = 0
        if isinstance(distance, (int, float)):
            rank_score = max(0, 20 - float(distance))
        candidates.append({
            "doc": doc,
            "origin": "semantic",
            "score": rank_score,
            "distance": distance,
        })

    return candidates, scores


def _retrieve(question: str, domain: str | None):
    intent = detect_retrieval_intent(question)
    exact = _exact_source_match(question)
    exact_docs = _source_chunks(exact["source_key"]) if exact else []

    if exact and intent == "source_lookup":
        docs = exact_docs
        matched_title = exact["matched_value"] if exact["match_type"] in {"title", "heading"} else "none"
        matched_filename = exact["matched_value"] if exact["match_type"] in {"filename", "source_stem", "source"} else "none"
        retrieval_mode = "exact filename" if matched_filename != "none" else "exact title"
        _debug(f"detected_intent={intent}")
        _debug(f"selected_domain={domain or 'none'}")
        _debug(f"matched_title={matched_title}")
        _debug(f"matched_filename={matched_filename}")
        _debug(f"retrieval_mode={retrieval_mode}")
        _debug("semantic_search_run=no")
        _debug(f"source_files={sorted({_source_key(doc['metadata']) for doc in docs})}")
        _debug(f"chunk_count={len(docs)}")
        _debug("short_circuit_reason=source_lookup_exact_match")
        return docs

    matches = _metadata_matches(question, domain=domain)
    semantic_run = True

    if intent == "advisory":
        semantic_candidates, scores = _semantic_candidates(question, k=10)
    elif domain:
        semantic_candidates, scores = _semantic_candidates(question, domain=domain, k=6)
        if len(semantic_candidates) < 2:
            fallback_candidates, fallback_scores = _semantic_candidates(question, k=6)
            semantic_candidates.extend(fallback_candidates)
            scores.extend(fallback_scores)
    else:
        semantic_candidates, scores = _semantic_candidates(question, k=6)

    candidates = []
    candidates.extend({"doc": doc, "origin": "exact", "score": 0} for doc in exact_docs)
    candidates.extend({"doc": doc, "origin": "metadata", "score": 0} for doc in matches)
    candidates.extend(semantic_candidates)

    ranked_candidates = rank_retrieval_candidates(candidates, intent=intent, limit=5, return_details=True)
    combined = [candidate["doc"] for candidate in ranked_candidates]

    mode = "metadata" if matches else "semantic"
    if exact and intent == "advisory":
        mode = "advisory blended"
    matched_title = (
        exact["matched_value"]
        if exact and exact["match_type"] in {"title", "heading"}
        else "none"
    )
    matched_filename = (
        exact["matched_value"]
        if exact and exact["match_type"] in {"filename", "source_stem", "source"}
        else "none"
    )
    final_chunks = []
    for index, candidate in enumerate(ranked_candidates, start=1):
        doc = candidate["doc"]
        metadata = metadata_for(doc)
        final_chunks.append({
            "order": index,
            "title": metadata.get("title", ""),
            "source": _source_key(metadata),
            "type": metadata.get("type") or metadata.get("doc_type", ""),
            "origin": candidate.get("origin", ""),
            "raw_score": candidate.get("raw_score", 0),
            "adjusted_score": candidate.get("adjusted_score", 0),
            "reasons": candidate.get("rank_reasons", []),
        })

    _debug(f"detected_intent={intent}")
    _debug(f"selected_domain={domain or 'none'}")
    _debug(f"matched_title={matched_title}")
    _debug(f"matched_filename={matched_filename}")
    _debug(f"exact_match_found={'yes' if exact else 'no'}")
    _debug(f"metadata_matches_found={len(matches)}")
    _debug(f"semantic_search_run={'yes' if semantic_run else 'no'}")
    _debug(f"retrieval_mode={mode}")
    _debug("short_circuit_reason=none")
    _debug(f"source_files={sorted({_source_key(doc['metadata'] if isinstance(doc, dict) else doc.metadata) for doc in combined})}")
    _debug(f"chunk_count={len(combined)}")
    for chunk in final_chunks:
        _debug(
            "final_chunk "
            f"order={chunk['order']} "
            f"file={chunk['source']} "
            f"title={chunk['title']} "
            f"type={chunk['type']} "
            f"origin={chunk['origin']} "
            f"raw_score={chunk['raw_score']} "
            f"adjusted_score={chunk['adjusted_score']} "
            f"reasons={chunk['reasons']}"
        )
    if scores:
        score_parts = [
            f"{doc.metadata.get('source_path', doc.metadata.get('source', 'unknown'))}:{score}"
            for doc, score in scores
        ]
        _debug(f"similarity_scores={score_parts}")

    return combined


def retrieve_and_answer(q: str) -> str:
    routing = route_info(q)
    intent = detect_retrieval_intent(q)
    docs = _retrieve(q, routing["domain"])
    context = _format_context(docs)
    if intent == "advisory":
        response_shape = (
            "For advisory/diagnostic questions, lead with the most specific trigger-action cards or examples in context. "
            "Use this structure:\n"
            "1. **What patterns are showing up**\n"
            "2. **Evidence from your situation**\n"
            "3. **What to do first**\n"
            "4. **What to say**\n"
            "5. **Artefact / meeting move**\n"
            "6. **Supporting frameworks**\n"
            "Do not lead with broad article frameworks when specific cards are available."
        )
    else:
        response_shape = (
            "Respond using:\n"
            "1. **Answer**\n"
            "2. **Why it matters**\n"
            "3. **Plays/Examples**"
        )

    prompt = ChatPromptTemplate.from_template(
        "{system}\n\nContext:\n{context}\n\n"
        "Use the provided source labels when grounding the answer. "
        "Distinguish confirmed facts from inferences or assumptions when the context is thin.\n\n"
        "{response_shape}\n\n"
        "User: {q}"
    ).format(system=routing["lens"], context=context, response_shape=response_shape, q=q)

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

        .wf-chat-title {
            display: flex !important;
            align-items: center !important;
            gap: 12px !important;
            margin: 12px 0 8px 6px !important;
            color: #1f2937 !important;
        }
        .wf-chat-title img {
            width: 44px !important;
            height: 44px !important;
            object-fit: contain !important;
            border-radius: 50% !important;
        }
        .wf-chat-title strong {
            display: block !important;
            font-size: 24px !important;
            line-height: 1.05 !important;
            letter-spacing: 0 !important;
        }
        .wf-chat-title span {
            display: block !important;
            color: #64748b !important;
            font-size: 12px !important;
            margin-top: 3px !important;
        }

        /* Chatbot fixed height with scroll */
        .chatbot-area {
            max-height: 200px !important;
            overflow-y: auto !important;
        }

        #wf-chat-shell {
            background: #ffffff !important;
            border: 1px solid rgba(17,24,39,0.12) !important;
            border-radius: 8px !important;
            box-shadow: 0 1px 5px rgba(15,23,42,0.08) !important;
            overflow: hidden !important;
        }
        #wf-chat-shell {
            position: relative !important;
        }
        #wf-chat-toolbar,
        #wf-chat-toolbar > div {
            position: absolute !important;
            top: 8px !important;
            right: 12px !important;
            z-index: 50 !important;
            display: flex !important;
            align-items: center !important;
            gap: 4px !important;
            background: rgba(255,255,255,0.92) !important;
            border: 1px solid rgba(15,23,42,0.14) !important;
            border-radius: 5px !important;
            box-shadow: 0 1px 4px rgba(15,23,42,0.12) !important;
            padding: 3px !important;
            min-width: 0 !important;
            width: auto !important;
        }
        #wf-chat-toolbar button,
        #wf-chat-toolbar .wf-tool-btn {
            width: auto !important;
            height: 26px !important;
            min-height: 26px !important;
            min-width: 42px !important;
            padding: 0 7px !important;
            margin: 0 !important;
            border: 0 !important;
            border-radius: 4px !important;
            background: transparent !important;
            color: #475569 !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
            box-shadow: none !important;
            font-size: 13px !important;
            line-height: 1 !important;
        }
        #wf-chat-toolbar button:hover,
        #wf-chat-toolbar .wf-tool-btn:hover {
            background: rgba(15,23,42,0.08) !important;
            color: #0f172a !important;
        }
        #wf-chat-toolbar svg {
            width: 17px !important;
            height: 17px !important;
            stroke: currentColor !important;
        }
        #wf-clear-hidden {
            display: none !important;
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

        gr.HTML(
            """
            <div class="wf-chat-title">
                <img src="/static/WAI_character.png" alt="WAI">
                <div>
                    <strong>WorkFriend Chatbot</strong>
                    <span>WAI - practical help for messy work</span>
                </div>
            </div>
            """
        )

        with gr.Group(elem_id="wf-chat-shell"):
            with gr.Row(elem_id="wf-chat-toolbar"):
                share_btn = gr.Button("Share", elem_classes=["wf-tool-btn"])
                clear_btn = gr.Button("Clear", elem_classes=["wf-tool-btn"])
                toolbar_copy_btn = gr.Button("Copy", elem_classes=["wf-tool-btn"])

            chatbot = gr.Chatbot(
                label="WorkFriend Conversation",
                height=200,
                elem_id="wf-chatbot",
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

        share_btn.click(
            None, None, None,
            js="""() => {
                const shareData = {title: document.title, url: window.location.href};
                if (navigator.share) {
                    navigator.share(shareData).catch(() => {});
                } else if (navigator.clipboard) {
                    navigator.clipboard.writeText(window.location.href);
                }
            }"""
        )
        clear_btn.click(lambda: ([], ""), None, [chatbot, user_input])
        toolbar_copy_btn.click(
            None, None, None,
            js="""() => {
                const scope = document.querySelector('#wf-chatbot') || document;
                const blocks = scope.querySelectorAll('.message, .chat-message, [data-testid=bot]');
                const text = blocks.length ? blocks[blocks.length - 1].innerText.trim() : '';
                if (text && navigator.clipboard) navigator.clipboard.writeText(text);
            }"""
        )
        send_btn.click(answer_fn, [user_input, chatbot], [chatbot, user_input])
        user_input.submit(answer_fn, [user_input, chatbot], [chatbot, user_input])

    return demo
