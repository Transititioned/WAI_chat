# ==========================================================
# loaders.py – Handles loading markdown files into chunks
# ==========================================================
from pathlib import Path
import re

print("📦 Initializing loaders module...")

DOMAIN_DIRS = {
    "articles": "articles",
    "wai_project_mgmt": "project_mgmt",
    "wai_change_mgmt_library": "change_mgmt",
    "data_mgmt_library": "data_gov",
}


def _parse_front_matter(text: str):
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    metadata = {}
    for line in parts[1].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')

    return metadata, parts[2].strip()


def _heading_path(text: str) -> str:
    headings = []
    for line in text.splitlines():
        match = re.match(r"^(#{1,3})\s+(.+)$", line.strip())
        if match:
            headings.append(match.group(2).strip())
        if len(headings) == 3:
            break
    return " > ".join(headings)


def _domain_for(path: Path, content_dir: Path) -> str:
    try:
        first_part = path.relative_to(content_dir).parts[0]
    except ValueError:
        first_part = path.parent.name
    return DOMAIN_DIRS.get(first_part, "general")


def _doc_type_for(path: Path, front_matter: dict) -> str:
    if front_matter.get("type"):
        return front_matter["type"]
    parts = {part.lower() for part in path.parts}
    if "cards" in parts:
        return "card"
    if "examples" in parts:
        return "example"
    if "articles" in parts:
        return "article"
    return "markdown"


def _iter_markdown_files(content_dir: Path):
    for root_name in DOMAIN_DIRS:
        root = content_dir / root_name
        if root.exists():
            yield from root.rglob("*.md")


def load_corpus_chunks(content_dir: Path, chunk_size: int = 1500):
    """
    Loads markdown from known corpus folders and adds domain/source metadata.
    """
    docs = []
    if not content_dir.exists():
        print(f"⚠️ Directory not found: {content_dir}")
        return docs

    md_files = sorted(_iter_markdown_files(content_dir))
    print(f"[DEBUG] Found {len(md_files)} corpus markdown files in {content_dir}")

    for md_file in md_files:
        try:
            raw_text = md_file.read_text(encoding="utf-8").strip()
            if not raw_text:
                print(f"⚠️ Skipping empty file: {md_file.name}")
                continue

            front_matter, text = _parse_front_matter(raw_text)
            if not text:
                continue

            relative_path = md_file.relative_to(content_dir).as_posix()
            base_metadata = {
                "source": md_file.name,
                "source_path": relative_path,
                "domain": _domain_for(md_file, content_dir),
                "doc_type": _doc_type_for(md_file, front_matter),
                "heading_path": _heading_path(text),
                "confidence": front_matter.get("confidence", "unspecified"),
            }

            for i in range(0, len(text), chunk_size):
                chunk = text[i:i + chunk_size]
                docs.append({
                    "content": chunk,
                    "metadata": {
                        **base_metadata,
                        "chunk_index": i // chunk_size,
                    }
                })
        except Exception as e:
            print(f"❌ Error reading {md_file.name}: {e}")

    print(f"📄 Loaded {len(docs)} text chunks from {len(md_files)} markdown files.")
    return docs


def load_markdown_chunks(articles_dir: Path, chunk_size: int = 1500):
    """
    Backwards-compatible loader for a single markdown directory.
    """
    if articles_dir.name == "content":
        return load_corpus_chunks(articles_dir, chunk_size=chunk_size)

    docs = []
    if not articles_dir.exists():
        print(f"⚠️ Directory not found: {articles_dir}")
        return docs

    md_files = sorted(articles_dir.glob("*.md"))
    print(f"[DEBUG] Found {len(md_files)} markdown files in {articles_dir}")

    for md_file in md_files:
        try:
            raw_text = md_file.read_text(encoding="utf-8").strip()
            if not raw_text:
                print(f"⚠️ Skipping empty file: {md_file.name}")
                continue

            front_matter, text = _parse_front_matter(raw_text)
            for i in range(0, len(text), chunk_size):
                docs.append({
                    "content": text[i:i + chunk_size],
                    "metadata": {
                        "source": md_file.name,
                        "source_path": md_file.name,
                        "domain": "articles",
                        "doc_type": _doc_type_for(md_file, front_matter),
                        "heading_path": _heading_path(text),
                        "confidence": front_matter.get("confidence", "unspecified"),
                        "chunk_index": i // chunk_size,
                    }
                })
        except Exception as e:
            print(f"❌ Error reading {md_file.name}: {e}")

    print(f"📄 Loaded {len(docs)} text chunks from {len(md_files)} markdown files.")
    return docs


print("✅ Loaders module ready.")
