import os
import gradio as gr
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA

# --- Configuration ---
INDEX_DIR = "index"
MODEL = "gpt-4o-mini"  # ✅ fixed typo: was "gpt-4o-m1ni"

# --- Load index and model ---
embedding = OpenAIEmbeddings()
vectordb = Chroma(persist_directory=INDEX_DIR, embedding_function=embedding)
retriever = vectordb.as_retriever(search_kwargs={"k": 3})
llm = ChatOpenAI(model=MODEL, temperature=0.3)

qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, chain_type="stuff")

def chat_fn(message, history):
    """Handles user queries"""
    try:
        result = qa_chain.run(message)
        return result
    except Exception as e:
        return f"⚠️ Error: {e}"

demo = gr.ChatInterface(
    fn=chat_fn,
    title="💬 Ask Workfriend",
    description="Ask Workfriend about articles and sensible tools for smart people.",
    examples=[
        "How to engage stakeholders?",
        "What is the main idea of 'The Map Is Not the Territory'?"
    ]
)

if __name__ == "__main__":
    demo.launch()
