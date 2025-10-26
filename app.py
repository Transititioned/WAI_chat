# app.py — same as your working chatbot, with correct Document objects
import os
from pathlib import Path
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# --- Configuration ---
ARTICLES_DIR = Path("content/articles")
INDEX_DIR = Path("index")
MODEL_NAME = "text-embedding-3-small"

# --- Embeddings & Index Setup ---
embedding = OpenAIEmbeddings(model=MODEL_NAME)

# ✅ Build a fresh index from markdown files (using Document objects)
print("🧱 Rebuilding Chroma index from markdown files...")
docs = []
for md_file in ARTICLES_DIR.glob("*.md"):
    text = md_file.read_text(encoding="utf-8")
    docs.append(Document(page_content=text, metadata={"source": md_file.name}))

vectordb = Chroma.from_documents(
    documents=docs,
    embedding=embedding,
    persist_directory=str(INDEX_DIR),
)
retriever = vectordb.as_retriever(search_kwargs={"k": 3})

# --- Chat Function ---
def ask_workfriend(query):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    docs = retriever.invoke(query)
    context = "\n\n".join([d.page_content for d in docs])
    prompt = f"Use the context below to answer clearly and concisely.\n\n{context}\n\nQuestion: {query}"
    return llm.invoke(prompt).content

# --- Run Locally (terminal test) ---
if __name__ == "__main__":
    print("✅ CaveBot ready!")
    while True:
        q = input("🔍 Ask: ")
        if q.lower() in ["exit", "quit"]:
            break
        print("💬 Answer:\n", ask_workfriend(q))
