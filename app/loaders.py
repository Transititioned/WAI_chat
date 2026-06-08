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

DOMAIN_ALIASES = {
    "change_management": "change_mgmt",
    "change-mgmt": "change_mgmt",
    "change management": "change_mgmt",
    "project_management": "project_mgmt",
    "project-management": "project_mgmt",
    "project management": "project_mgmt",
    "data_management": "data_gov",
    "data-management": "data_gov",
    "data management": "data_gov",
    "data_governance": "data_gov",
    "data governance": "data_gov",
}


def _parse_front_matter(text: str):
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    metadata = {}
    current_key = None
    for raw_line in parts[1].splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith(("-", "*")) and current_key:
            item = line[1:].strip().strip('"').strip("'")
            existing = metadata.get(current_key)
            if isinstance(existing, list):
                existing.append(item)
            elif existing:
                metadata[current_key] = [existing, item]
            else:
                metadata[current_key] = [item]
            continue

        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        current_key = key

        if value.startswith("[") and value.endswith("]"):
            metadata[key] = [
                item.strip().strip('"').strip("'")
                for item in value[1:-1].split(",")
                if item.strip()
            ]
        else:
            metadata[key] = value.strip('"').strip("'")

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


def _normalize_domain(domain: str) -> str:
    if not domain:
        return "general"
    normalized = domain.strip().lower().replace("-", "_")
    return DOMAIN_ALIASES.get(normalized, normalized)


def _metadata_value(front_matter: dict, key: str, default: str = ""):
    value = front_matter.get(key, default)
    if isinstance(value, list):
        return ", ".join(item for item in value if item)
    return value


def _title_for(path: Path, front_matter: dict, heading_path: str) -> str:
    title = _metadata_value(front_matter, "title")
    if title:
        return title
    if heading_path:
        return heading_path.split(" > ", 1)[0]
    return path.stem.replace("_", " ").replace("-", " ")


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
            inferred_domain = _domain_for(md_file, content_dir)
            domain = _normalize_domain(front_matter.get("domain", inferred_domain))
            doc_type = _doc_type_for(md_file, front_matter)
            tags = _metadata_value(front_matter, "tags")
            heading_path = _heading_path(text)
            base_metadata = {
                "title": _title_for(md_file, front_matter, heading_path),
                "source": md_file.name,
                "source_filename": md_file.name,
                "source_path": relative_path,
                "domain": domain,
                "type": doc_type,
                "doc_type": doc_type,
                "tags": tags,
                "status": _metadata_value(front_matter, "status", "unspecified"),
                "secondary_domains": _metadata_value(front_matter, "secondary_domains"),
                "stage": _metadata_value(front_matter, "stage"),
                "trigger_phrases": _metadata_value(front_matter, "trigger_phrases"),
                "retrieval_intent": _metadata_value(front_matter, "retrieval_intent"),
                "id": _metadata_value(front_matter, "id"),
                "heading_path": heading_path,
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
            doc_type = _doc_type_for(md_file, front_matter)
            tags = _metadata_value(front_matter, "tags")
            heading_path = _heading_path(text)
            for i in range(0, len(text), chunk_size):
                docs.append({
                    "content": text[i:i + chunk_size],
                    "metadata": {
                        "title": _title_for(md_file, front_matter, heading_path),
                        "source": md_file.name,
                        "source_filename": md_file.name,
                        "source_path": md_file.name,
                        "domain": "articles",
                        "type": doc_type,
                        "doc_type": doc_type,
                        "tags": tags,
                        "status": _metadata_value(front_matter, "status", "unspecified"),
                        "secondary_domains": _metadata_value(front_matter, "secondary_domains"),
                        "stage": _metadata_value(front_matter, "stage"),
                        "trigger_phrases": _metadata_value(front_matter, "trigger_phrases"),
                        "retrieval_intent": _metadata_value(front_matter, "retrieval_intent"),
                        "id": _metadata_value(front_matter, "id"),
                        "heading_path": heading_path,
                        "confidence": front_matter.get("confidence", "unspecified"),
                        "chunk_index": i // chunk_size,
                    }
                })
        except Exception as e:
            print(f"❌ Error reading {md_file.name}: {e}")

    print(f"📄 Loaded {len(docs)} text chunks from {len(md_files)} markdown files.")
    return docs


print("✅ Loaders module ready.")
