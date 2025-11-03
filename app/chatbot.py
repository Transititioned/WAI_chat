# ==========================================================
# app/chatbot.py
# ----------------------------------------------------------
# Purpose:
#   WorkFriend Chatbot (CaveBot core)
#   - Uses LangChain RAG over Markdown corpus
#   - Modular floating user actions: Retry, Copy, Voice Input
#   - Safe with Hugging Face + Gradio 4.x
# ==========================================================

import gradio as gr
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from pathlib import Path
from app.chatbot_actions import add_floating_actions  # ✅ Modular import


def init_chatbot():
    """Initialize and return the Gradio chatbot interface (stable tuple format)."""
    # --- Paths and setup ---
    ARTICLES_DIR = Path("content/articles")
    if not ARTICLES_DIR.exists():
        ARTICLES_DIR = Path(".")
    INDEX_DIR = Path("index")

    # --- LLM setup ---
    openai_key = os.getenv("OPENAI_API_KEY")
    embedding = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=openai_key)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, openai_api_key=openai_key)

    # --- Build vector store from markdown files ---
