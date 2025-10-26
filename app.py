import os
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# --- Configuration ---
ARTICLES_DIR = Path("content/articles")
MODEL_NAME = "text-embedding-3-small"

# --- API key check ---
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    raise EnvironmentError(
        "❌ OPENAI_API_KEY not found. Add it under 'Settings → Variables' in your Hugging Face Space."
    )

# --- Initialize OpenAI tools ---
embedding = OpenAIEmbeddings(model=MODEL_NAME, openai_api_key=openai_key)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, openai_api_key=openai_key)

# --- Load markdown and build in-memory index ---
print("🧱 Building in-memory Chroma index from markdown files...")
docs, metadatas = [], []

for md_file in ARTICLES_DIR.glob("*.md"):
    text = md_file.read_text(encoding="utf-8")
    chunks = [text[i:i + 1500] for i in range(0, len(text), 1500)]
    for i, chunk in enumerate(chunks):
        docs.append(chunk)
        metadatas.append({"source": md_file.name})

vectordb = Chroma.from_texts(
    texts=docs,
    embedding=embedding,
    metadatas=metadatas,      # no persist_directory → purely in memory
)
retriever = vectordb.as_retriever(search_kwargs={"k": 3})

# --- Prompt template ---
prompt = ChatPromptTemplate.from_template(
    "Use the following context to answer clearly and concisely.\n\n"
    "Context:\n{context}\n\nQuestion:\n{question}"
)

def retrieve_and_answer(question: str):
    retrieved = retriever.invoke(question)
    if not retrieved:
        return "⚠️ No relevant content found in the index."
    context = "\n\n".join([d.page_content for d in retrieved])
    filled_prompt = prompt.format(context=context, question=question)
    response = llm.invoke(filled_prompt)
    return response.content

# --- CLI entrypoint (works in HF console) ---
if __name__ == "__main__":
    print("✅ CaveBot ready! (In-memory index)")
    while True:
        query = input("🔍 Ask: ")
        if query.lower() in ["exit", "quit"]:
            break
        print("💬 Answer:\n", retrieve_and_answer(query))
