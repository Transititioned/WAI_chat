# ==========================================================
# vectorstore.py – Build or load Chroma index with debug logs
# ==========================================================
import os
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

from . import config
from . import loaders

print("🧩 Initializing vectorstore module...")

def init_vectorstore():
    """Builds or loads Chroma index for markdown documents with verbose debug output."""
    try:
        print(f"[DEBUG] INDEX_DIR={config.INDEX_DIR}")
        print(f"[DEBUG] ARTICLES_DIR={config.ARTICLES_DIR}")
        print(f"[DEBUG] OPENAI_KEY={'YES' if config.OPENAI_KEY else 'NO'}")

        # Load markdown docs
        docs = loaders.load_markdown_chunks(config.ARTICLES_DIR)
        print(f"[DEBUG] Loaded {len(docs)} total markdown chunks.")

        if not docs:
            print("⚠️ No markdown files found — skipping vectorstore build.")
            return None

        # Init embeddings
        embedding_model = "text-embedding-3-small"
        print(f"[DEBUG] Initializing embeddings model: {embedding_model}")
        embeddings = OpenAIEmbeddings(model=embedding_model, openai_api_key=config.OPENAI_KEY)
        print("[DEBUG] Embeddings initialized successfully.")

        # Load or create vector index
        if config.INDEX_DIR.exists() and any(config.INDEX_DIR.iterdir()):
            print("🗂️ Existing Chroma index detected, attempting to load...")
            vectordb = Chroma(persist_directory=str(config.INDEX_DIR), embedding_function=embeddings)
            print("✅ Existing Chroma index loaded successfully.")
        else:
            print("🧱 No Chroma index found, building a new one...")
            vectordb = Chroma.from_texts(
                texts=[d["content"] for d in docs],
                embedding=embeddings,
                metadatas=[d["metadata"] for d in docs],
                persist_directory=str(config.INDEX_DIR)
            )
            vectordb.persist()
            print("✅ New Chroma index created and persisted.")

        print("[DEBUG] Vectorstore initialization complete.")
        return vectordb

    except Exception as e:
        print(f"❌ Error initializing vectorstore: {e}")
        return None
