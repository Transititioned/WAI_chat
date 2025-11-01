# ==========================================================
# loaders.py – Handles loading markdown files into chunks
# ==========================================================
from pathlib import Path

print("📦 Initializing loaders module...")

def load_markdown_chunks(articles_dir: Path, chunk_size: int = 1500):
    """
    Loads markdown (.md) files from a directory and splits them into text chunks.
    Each chunk is returned with metadata linking it back to its source file.
    """
    docs = []
    if not articles_dir.exists():
        print(f"⚠️ Directory not found: {articles_dir}")
        return docs

    md_files = list(articles_dir.glob("*.md"))
    print(f"[DEBUG] Found {len(md_files)} markdown files in {articles_dir}")

    for md_file in md_files:
        try:
            text = md_file.read_text(encoding="utf-8").strip()
            if not text:
                print(f"⚠️ Skipping empty file: {md_file.name}")
                continue

            chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
            for chunk in chunks:
                docs.append({
                    "content": chunk,
                    "metadata": {"source": md_file.name}
                })
        except Exception as e:
            print(f"❌ Error reading {md_file.name}: {e}")

    print(f"📄 Loaded {len(docs)} text chunks from {len(md_files)} markdown files.")
    return docs

print("✅ Loaders module ready.")
