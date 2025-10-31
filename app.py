# ==========================================================
# CaveBot – Austonian merge build v0.3.7-dev (messages mode, HF-stable)
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

# ==========================================================
# 2. Configuration
# ==========================================================
ARTICLES_DIR = Path("content/articles")
if not ARTICLES_DIR.exists():
    ARTICLES_DIR = Path(".")
INDEX_DIR = Path("index")

MODEL_EMBED = "text-embedding-3-small"
MODEL_CHAT = "gpt-4o-mini"

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

print("🧱 Rebuilding Chroma index from markdown files...")
docs = load_markdown_chunks(ARTICLES_DIR)
print(f"🔍 Found {len(docs)} markdown chunks from {len(list(ARTICLES_DIR.glob('*.md')))} files.")

# ==========================================================
# 4. Vector store
# ==========================================================
embedding = OpenAIEmbeddings(model=MODEL_EMBED, openai_api_key=openai_key)

if INDEX_DIR.exists() and any(INDEX_DIR.iterdir()):
    vectordb = Chroma(persist_directory=str(INDEX_DIR), embedding_function=embedding)
    print("✅ Loaded existing Chroma index.")
else:
    vectordb = Chroma.from_texts(
        texts=[d["content"] for d in docs],
        embedding=embedding,
        metadatas=[d["metadata"] for d in docs],
        persist_directory=str(INDEX_DIR)
    )
    print("✅ New Chroma index created and persisted.")

retriever = vectordb.as_retriever(search_kwargs={"k": 3})

# ==========================================================
# 5. LLM + prompt
# ==========================================================
llm = ChatOpenAI(model=MODEL_CHAT, temperature=0.3, openai_api_key=openai_key)

prompt_template = ChatPromptTemplate.from_template("""
You are CaveBot — a helpful, concise assistant trained on Kev’s markdown knowledge base.
If you don't know something, say "I don't know" instead of inventing details.

Context:
{context}

Conversation so far:
{history}

User question:
{question}

Answer clearly and in a friendly, professional tone.
""")

# ==========================================================
# 6. Retrieval + generation
# ==========================================================
def retrieve_and_answer(question: str, history: list):
    retrieved_docs = retriever.invoke(question)
    context = "\n\n".join([d.page_content for d in retrieved_docs])
    history_str = "\n".join([f"User: {u}\nBot: {b}" for u, b in history])
    filled_prompt = prompt_template.format(context=context, question=question, history=history_str)
    response = llm.invoke(filled_prompt)
    return response.content

# ==========================================================
# 7. Chat interface (new messages mode)
# ==========================================================
def answer_fn(message, history, request=None):
    try:
        answer = retrieve_and_answer(message, history)
        # Gradio automatically updates history in 'messages' mode;
        # returning a plain string keeps everything in sync
        return answer
    except Exception as e:
        return f"⚠️ Error: {e}"

demo = gr.ChatInterface(
    fn=answer_fn,
    title="CaveBot v0.3.7-dev",
    description="Ask about my markdown knowledge base",
    chatbot=gr.Chatbot(type="messages"),  # ✅ modern mode
    theme="soft",
)

# ==========================================================
# 8. Run
# ==========================================================
if __name__ == "__main__":
    demo.launch()
