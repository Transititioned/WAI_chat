import os
from pathlib import Path
import gradio as gr
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

ARTICLES_DIR = Path("content/articles")
EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError("Add OPENAI_API_KEY in Space → Settings → Variables")

llm = ChatOpenAI(model=CHAT_MODEL, temperature=0.3, openai_api_key=OPENAI_API_KEY)
_embedding = None
_vectordb = None
_index_built = False

def build_index_once():
    global _embedding, _vectordb, _index_built
    if _index_built:
        return
    print("🧠 Building index…")
    _embedding = OpenAIEmbeddings(model=EMBED_MODEL, openai_api_key=OPENAI_API_KEY)
    texts, metas = [], []
    for f in ARTICLES_DIR.glob("*.md"):
        txt = f.read_text(encoding="utf-8")
        for i in range(0, len(txt), 1500):
            chunk = txt[i:i+1500]
            if chunk.strip():
                texts.append(chunk)
                metas.append({"source": f.name})
    if not texts:
        raise RuntimeError("No text found in markdown files")
    _vectordb = Chroma.from_texts(texts=texts, embedding=_embedding, metadatas=metas)
    _index_built = True
    print(f"✅ Built index with {len(texts)} chunks")

prompt = ChatPromptTemplate.from_template(
    "Use the following context to answer clearly.\n\nContext:\n{context}\n\nQuestion:\n{question}"
)

def answer_fn(question: str):
    try:
        if not _index_built:
            build_index_once()
        retriever = _vectordb.as_retriever(search_kwargs={"k": 3})
        docs = retriever.invoke(question)
        if not docs:
            return "⚠️ No relevant content found."
        context = "\n\n".join(d.page_content for d in docs)
        filled = prompt.format(context=context, question=question)
        resp = llm.invoke(filled)
        return resp.content
    except Exception as e:
        return f"🚨 {e}"

# Gradio interface (the key piece HF needs)
demo = gr.ChatInterface(fn=answer_fn, title="🧠 CaveBot", description="Ask about my markdown knowledge base")

if __name__ == "__main__":
    demo.launch()
