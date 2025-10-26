import os
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain.docstore.document import Document

# --- Configuration ---
ARTICLES_DIR = Path("content/articles")
INDEX_DIR = Path("index")
MODEL_NAME = "text-embedding-3-small"

# --- Embeddings & model ---
embedding = OpenAIEmbeddings(model=MODEL_NAME, openai_api_key=os.getenv("OPENAI_API_KEY"))
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, openai_api_key=os.getenv("OPENAI_API_KEY"))

# --- Rebuild Chroma index ---
print("🧱 Rebuilding Chroma index from markdown files...")

docs = []
for md_file in ARTICLES_DIR.glob("*.md"):
    text = md_file.read_text(encoding="utf-8")
    chunks = [text[i:i + 1500] for i in range(0, len(text), 1500)]
    for i, chunk in enumerate(chunks):
        docs.append(Document(page_content=chunk, metadata={"source": md_file.name}))

vectordb = Chroma.from_documents(
    documents=docs,
    embedding=embedding,
    persist_directory=str(INDEX_DIR)
)

retriever = vectordb.as_retriever(search_kwargs={"k": 3})

# --- Create a simple retrieval chain ---
prompt = ChatPromptTemplate.from_template(
    "Use the following context to answer concisely:\n\n{context}\n\nQuestion: {question}"
)

qa_chain = (
    {"context": retriever | (lambda docs: "\n\n".join(d.page_content for d in docs)), "question": RunnablePassthrough()}
    | prompt
    | llm
)

print("✅ CaveBot ready!")
while True:
    query = input("🔍 Ask: ")
    if query.lower() in ["exit", "quit"]:
        break
    answer = qa_chain.invoke({"question": query})
    print("💬 Answer:\n", answer.content)
