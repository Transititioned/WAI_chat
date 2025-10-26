import os
from pathlib import Path
import gradio as gr
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA

# --- Configuration ---
ARTICLES_DIR = Path(".")  # markdowns live at repo root on Hugging Face
INDEX_DIR = Path("index")
MODEL_EMBEDDING = "text-embedding-3-small"
MODEL_CHAT = "gpt-4o-mini"

# --- Validate environment ---
if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("Missing OPENAI_API_KEY environment variable.")

# --- Load markdown files ---
md_files = list(ARTICLES_DIR.glob("*.md"))
if not md_files:
    raise RuntimeError(f"No markdown files found in {ARTICLES_DIR.resolve()}")

print("🧱 Rebuilding Chroma index from markdown files...")
print("Found files:", [f.name for f in md_files])

# --- Build documents ---
docs = []
for f in md_files:
    text = f.read_text(encoding="utf-8").strip()
    if text:
        chunks = [text[i:i+1500] for i in range(0, len(text), 1500)]
        for i, chunk in enumerate(chunks):
            docs.append({
                "page_content": chunk,
                "metadata": {"source": f.name, "chunk_id": i}
            })
    else:
        print(f"⚠️ Skipping empty file: {f.name}")

# --- Initialize embeddings and vector store ---
embedding = OpenAIEmbeddings(model=MODEL_EMBEDDING)

texts = [d["page_content"] for d in docs]
metadatas = [d["metadata"] for d in docs]
ids = [f"{m['source']}-{m['chunk_id']}" for m in metadatas]

vectordb = Chroma.from_texts(
    texts=texts,
    embedding=embedding,
    metadatas=metadatas,
    ids=ids,
    persist_directory=str(INDEX_DIR)
)

retriever = vectordb.as_retriever(search_kwargs={"k": 3})
llm = ChatOpenAI(model=MODEL_CHAT, temperature=0.3)
qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, chain_type="stuff")

print("✅ CaveBot ready!")

# --- Chat logic ---
def chat_fn(message, history):
    """Handles user queries."""
    try:
        result = qa_chain.run(message)
        return result
    except Exception as e:
        return f"⚠️ Error: {e}"

# --- Gradio interface ---
demo = gr.ChatInterface(
    fn=chat_fn,
    title="🕐 Ask Workfriend",
    description="Ask Workfriend about sensible tools for smart people.",
    examples=[
        "How to engage stakeholders?",
        "What's the main message of 'The Map Is Not the Territory'?",
        "What's a good tip for managing vendor relationships?"
    ],
)

if __name__ == "__main__":
    demo.launch()
