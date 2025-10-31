# ==========================================================
# CaveBot – Austonian merge build v0.3.8-dev
# ✅ Debug + verified messages-mode integration for HF Spaces
# ==========================================================
import os
from pathlib import Path
from dotenv import load_dotenv

import gradio as gr
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


# ==========================================================
# 1. Environment
# ==========================================================
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
print(f"[DEBUG] OpenAI key detected: {'YES' if openai_key else 'NO'}")

# ==========================================================
# 2. Configuration
# ==========================================================
ARTICLES_DIR = Path("content/articles")
if not ARTICLES_DIR.exists():
    ARTICLES_DIR = Path(".")
INDEX_DIR = Path("index")

MODEL_EMBED = "text-embedding-3-small"
MODEL_CHAT = "gpt-4o-mini"

print(f"[DEBUG] ARTICLES_DIR={ARTICLES_DIR.resolve()}")
print(f"[DEBUG] INDEX_DIR={INDEX_DIR.resolve()}")


# ==========================================================
# 3. Loader
# ==========================================================
def load_markdown_chunks(articles_dir: Path, chunk_size: int = 1500):
    docs = []
    for md_file in articles_dir.glob("*.md"):
        text = md_file.read_text(encoding="utf-8").strip()
        if not text:
            continue
        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
        for chunk in chunks:
            docs.append({"content": chunk, "metadata": {"source": md_file.name}})
    return docs


print("[DEBUG] Loading markdown chunks…")
docs = load_markdown_chunks(ARTICLES_DIR)
print(f"[DEBUG] Loaded {len(docs)} chunks from {len(list(ARTICLES_DIR.glob('*.md')))} file(s).")


# ==========================================================
# 4. Vector store
# ==========================================================
embedding = OpenAIEmbeddings(model=MODEL_EMBED, openai_api_key=openai_key)
print("[DEBUG] Embedding model initialised")

if INDEX_DIR.exists() and any(INDEX_DIR.iterdir()):
    vectordb = Chroma(persist_directory=str(INDEX_DIR), embedding_function=embedding)
    print(f"[DEBUG] Existing Chroma index loaded from {INDEX_DIR}")
else:
    vectordb = Chroma.from_texts(
        texts=[d["content"] for d in docs],
        embedding=embedding,
        metadatas=[d["metadata"] for d in docs],
        persist_directory=str(INDEX_DIR)
    )
    print(f"[DEBUG] New Chroma index built and persisted at {INDEX_DIR}")

retriever = vectordb.as_retriever(search_kwargs={"k": 3})
print("[DEBUG] Retriever ready (k=3)")


# ==========================================================
# 5. LLM + prompt
# ==========================================================
llm = ChatOpenAI(model=MODEL_CHAT, temperature=0.3, openai_api_key=openai_key)
print(f"[DEBUG] ChatOpenAI initialised: {MODEL_CHAT}")

prompt_template = ChatPromptTemplate.from_template("""
You are CaveBot — a concise, friendly assistant trained on Kev’s markdown knowledge base.
If you don't know something, say "I don't know" instead of inventing details.

Context:
{context}

Conversation so far:
{history}

User question:
{question}

Answer in a helpful, professional tone.
""")
print("[DEBUG] Prompt template ready")


# ==========================================================
# 6. Retrieval + generation
# ==========================================================
def retrieve_and_answer(question: str, history: list):
    print(f"[DEBUG] retrieve_and_answer() called: question={question!r}, history_len={len(history)}")

    # --- History normalisation (tuples -> dicts) ---
    if history and isinstance(history[0], (list, tuple)):
        print("[DEBUG] Normalising tuple-based history to dict format")
        converted = []
        for u, b in history:
            converted.append({"role": "user", "content": u})
            converted.append({"role": "assistant", "content": b})
        history = converted

    # --- Retrieval ---
    retrieved_docs = retriever.invoke(question)
    context = "\n\n".join([d.page_content for d in retrieved_docs])
    print(f"[DEBUG] Retrieved {len(retrieved_docs)} docs. Context preview: {context[:120]!r}")

    # --- Prompt construction ---
    history_str = ""
    if history:
        try:
            history_str = "\n".join([f"{m['role'].title()}: {m['content']}" for m in history])
        except Exception:
            history_str = str(history)
    filled_prompt = prompt_template.format(context=context, question=question, history=history_str)
    print(f"[DEBUG] Filled prompt preview: {filled_prompt[:200]!r}")

    # --- LLM call ---
    response = llm.invoke(filled_prompt)
    print(f"[DEBUG] LLM response object: {response!r}")
    return response.content


# ==========================================================
# 7. Chat interface (messages-mode, debug)
# ==========================================================
def answer_fn(message, history, request=None):
    print("=" * 60)
    print(f"[DEBUG] answer_fn() called → message={message!r}")
    print(f"[DEBUG] history object type={type(history)}, length={len(history)}")
    try:
        answer = retrieve_and_answer(message, history)
        print(f"[DEBUG] Returning answer len={len(answer)} chars")
        return answer
    except Exception as e:
        print(f"[ERROR] Exception in answer_fn: {e}")
        return f"⚠️ Error: {e}"


demo = gr.ChatInterface(
    fn=answer_fn,
    type="messages",
    title="CaveBot v0.3.8-dev",
    description="Ask about my markdown knowledge base (debug build)",
    chatbot=gr.Chatbot(type="messages"),
    theme="soft",
)

print("[DEBUG] Gradio ChatInterface created — launching…")


# ==========================================================
# 8. Run
# ==========================================================
if __name__ == "__main__":
    demo.launch()
