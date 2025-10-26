import os
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import gradio as gr

# --- Configuration ---
ARTICLES_DIR = Path("content/articles")
MODEL_NAME = "text-embedding-3-small"

# --- Adjust if folder missing ---
if not ARTICLES_DIR.exists():
    ARTICLES_DIR = Path(".")  # fallback to repo root

INDEX_DIR = Path("index")

# --- Embeddings & model ---
openai_key = os.getenv("OPENAI_API_KEY")
embedding = OpenAIEmbeddings(model=MODEL_NAME, openai_api_key=openai_key)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, openai_api_key=openai_key)

# --- Build documents ---
print("🧱 Rebuilding Chroma index from markdown files...")

docs = []
for md_file in ARTICLES_DIR.glob("*.md"):
    text = md_file.read_text(encoding="utf-8").strip()
    if not text:
        continue
    chunks = [text[i:i + 1500] for i in range(0, len(text), 1500)]
    for chunk in chunks:
        docs.append({"content": chunk, "metadata": {"source": md_file.name}})

print(f"🔍 Found {len(docs)} markdown chunks from {len(list(ARTICLES_DIR.glob('*.md')))} files.")
if not docs:
    raise ValueError(f"❌ No markdowns found in {ARTICLES_DIR.resolve()}")

# --- Create vector index ---
vectordb = Chroma.from_texts(
    texts=[d["content"] for d in docs],
    embedding=embedding,
    metadatas=[d["metadata"] for d in docs],
)
retriever = vectordb.as_retriever(search_kwargs={"k": 3})

# --- Define retrieval + generation chain ---
prompt = ChatPromptTemplate.from_template(
    "Use the following context to answer clearly and concisely:\n\n{context}\n\nQuestion: {question}"
)

def retrieve_and_answer(question: str):
    retrieved_docs = retriever.invoke(question)
    context = "\n\n".join([d.page_content for d in retrieved_docs])
    filled_prompt = prompt.format(context=context, question=question)
    response = llm.invoke(filled_prompt)
    return response.content

# --- Gradio wiring (fixed argument signature) ---
def answer_fn(message, history):
    try:
        return retrieve_and_answer(message)
    except Exception as e:
        return f"⚠️ Error: {e}"

demo = gr.ChatInterface(
    fn=answer_fn,
    title="CaveBot",
    description="Ask about my markdown knowledge base",
    chatbot=gr.Chatbot(type="messages"),
)

if __name__ == "__main__":
    demo.launch()
