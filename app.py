import os
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# --- Configuration ---
ARTICLES_DIR = Path("content/articles")
INDEX_DIR = Path("index")
MODEL_NAME = "text-embedding-3-small"

# --- Embeddings & model ---
openai_key = os.getenv("OPENAI_API_KEY")
embedding = OpenAIEmbeddings(model=MODEL_NAME, openai_api_key=openai_key)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, openai_api_key=openai_key)

# --- Build documents ---
print("🧱 Rebuilding Chroma index from markdown files...")

docs = []
for md_file in ARTICLES_DIR.glob("*.md"):
    text = md_file.read_text(encoding="utf-8")
    chunks = [text[i:i + 1500] for i in range(0, len(text), 1500)]
    for i, chunk in enumerate(chunks):
        docs.append({"content": chunk, "metadata": {"source": md_file.name}})

# --- Create vector index ---
vectordb = Chroma.from_texts(
    texts=[d["content"] for d in docs],
    embedding=embedding,
    metadatas=[d["metadata"] for d in docs],
    persist_directory=str(INDEX_DIR)
)
retriever = vectordb.as_retriever(search_kwargs={"k": 3})

# --- Define minimal retrieval+generation chain ---
prompt = ChatPromptTemplate.from_template(
    "Use the following context to answer clearly and concisely:\n\n{context}\n\nQuestion: {question}"
)

def retrieve_and_answer(question: str):
    retrieved_docs = retriever.invoke(question)
    context = "\n\n".join([d.page_content for d in retrieved_docs])
    filled_prompt = prompt.format(context=context, question=question)
    response = llm.invoke(filled_prompt)
    return response.content

print("✅ CaveBot ready!")
while True:
    query = input("🔍 Ask: ")
    if query.lower() in ["exit", "quit"]:
        break
    print("💬 Answer:\n", retrieve_and_answer(query))
