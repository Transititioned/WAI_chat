import os
import sys
from pathlib import Path
from typing import List

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# ── CONFIG ─────────────────────────────────────────────────────────────────────
PREFERRED_ARTICLES_DIRS: List[Path] = [Path("content/articles"), Path(".")]
EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"

# ── ENV / SECRET CHECK ─────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError(
        "❌ OPENAI_API_KEY not found. Add it in the Space: Settings → Repository secrets."
    )

# ── DIAGNOSTICS (safe: no embedding call here) ─────────────────────────────────
def log_startup_diagnostics():
    print("── Startup Diagnostics ─────────────────────────")
    print(f"Python: {sys.version.split()[0]}")
    try:
        import chromadb, langchain_openai, langchain_community, langchain_core, tiktoken, gradio
        print(f"chromadb: {getattr(chromadb, '__version__', 'unknown')}")
        print(f"langchain-openai: {getattr(langchain_openai, '__version__', 'unknown')}")
        print(f"langchain-community: {getattr(langchain_community, '__version__', 'unknown')}")
        print(f"langchain-core: {getattr(langchain_core, '__version__', 'unknown')}")
        print(f"tiktoken: {getattr(tiktoken, '__version__', 'unknown')}")
        print(f"gradio: {getattr(gradio, '__version__', 'unknown')}")
    except Exception as e:
        print(f"⚠️ Version check error: {e}")

    print(f"OPENAI_API_KEY present: {'yes' if OPENAI_API_KEY else 'no'} (len={len(OPENAI_API_KEY) if OPENAI_API_KEY else 0})")

    chosen_dir = None
    for candidate in PREFERRED_ARTICLES_DIRS:
        files = list(candidate.glob("*.md"))
        if files:
            chosen_dir = candidate
            break
    print(f"Article dir candidates: {[str(p) for p in PREFERRED_ARTICLES_DIRS]}")
    print(f"Chosen articles dir: {str(chosen_dir.resolve()) if chosen_dir else 'None found'}")
    if chosen_dir:
        print("Markdown files:", [f.name for f in files])
    print("───────────────────────────────────────────────")

    return chosen_dir, files if chosen_dir else []

ARTICLES_DIR, ARTICLE_FILES = log_startup_diagnostics()
if not ARTICLE_FILES:
    raise RuntimeError("❌ No markdown files found in any of: " + ", ".join(str(p) for p in PREFERRED_ARTICLES_DIRS))

# ── LLM (safe at import; just a client wrapper) ────────────────────────────────
llm = ChatOpenAI(model=CHAT_MODEL, temperature=0.3, openai_api_key=OPENAI_API_KEY)

# ── LAZY INDEX (embeddings happen only when first query arrives) ──────────────
_embedding = None
_vectordb = None
_index_built = False

def build_index_once():
    """Build an in-memory Chroma index lazily and only once."""
    global _embedding, _vectordb, _index_built
    if _index_built:
        return

    print("🧠 Building Chroma index (lazy, runtime)…")
    _embedding = OpenAIEmbeddings(model=EMBED_MODEL, openai_api_key=OPENAI_API_KEY)

    texts, metas = [], []
    for md_file in ARTICLE_FILES:
        text = md_file.read_text(encoding="utf-8")
        if not text.strip():
            continue
        # simple fixed-size splitter
        chunks = [text[i:i+1500] for i in range(0, len(text), 1500)]
        for chunk in chunks:
            texts.append(chunk)
            metas.append({"source": md_file.name})

    if not texts:
        raise RuntimeError("❌ Articles loaded but produced no non-empty chunks.")

    # In-memory index: no persist_directory
    _vectordb = Chroma.from_texts(texts=texts, embedding=_embedding, metadatas=metas)
    _index_built = True
    print(f"✅ Index built with {len(texts)} chunks from {len(ARTICLE_FILES)} files.")

def retrieve_and_answer(question: str) -> str:
    try:
        if not _index_built:
            build_index_once()

        retriever = _vectordb.as_retriever(search_kwargs={"k": 3})
        docs = retriever.invoke(question)
        if not docs:
            return "⚠️ No relevant content found."

        context = "\n\n".join(d.page_content for d in docs)
        prompt = ChatPromptTemplate.from_template(
            "Use the following context to answer clearly and concisely.\n\n"
            "Context:\n{context}\n\nQuestion:\n{question}"
        )
        filled = prompt.format(context=context, question=question)
        resp = llm.invoke(filled)
        return resp.content
    except Exception as e:
        return f"🚨 Error: {e}"

# ── CLI entrypoint (keeps Space alive and testable) ────────────────────────────
if __name__ == "__main__":
    print("✅ CaveBot ready! (lazy, in-memory index; embeddings only after first question)")
    while True:
        try:
            q = input("🔍 Ask: ")
        except EOFError:
            break
        if q.strip().lower() in {"exit", "quit"}:
            break
        print("💬 Answer:\n", retrieve_and_answer(q))
