from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.loaders import load_corpus_chunks
from app.router import route_info



def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    docs = load_corpus_chunks(ROOT / "content")
    domains = {doc["metadata"].get("domain") for doc in docs}

    require("project_mgmt" in domains, "project management corpus was not loaded")
    require("change_mgmt" in domains, "change management corpus was not loaded")
    require("data_gov" in domains, "data management corpus was not loaded")
    require("articles" in domains, "articles corpus was not loaded")

    change_docs = [doc for doc in docs if doc["metadata"].get("domain") == "change_mgmt"]
    require(
        any("resistance" in doc["metadata"].get("source", "").lower() for doc in change_docs),
        "expected change-management resistance source was not indexed",
    )

    require(route_info("How do I handle stakeholder resistance?")["domain"] == "change_mgmt",
            "change-management routing failed")
    require(route_info("What should a kickoff checklist include?")["domain"] == "project_mgmt",
            "project-management routing failed")
    require(route_info("How do we improve metadata quality?")["domain"] == "data_gov",
            "data-governance routing failed")

    taking_the_wheel = [
        doc for doc in docs
        if doc["metadata"].get("source") == "taking_the_wheel.md"
    ]
    require(taking_the_wheel, "Taking the Wheel article was not indexed")
    require(
        taking_the_wheel[0]["metadata"].get("title") == "Taking the Wheel: The Art of the Project Takeover",
        "frontmatter title was not attached to article chunks",
    )
    require(
        "project-delivery" in taking_the_wheel[0]["metadata"].get("tags", ""),
        "frontmatter tags were not attached to article chunks",
    )

    with tempfile.TemporaryDirectory() as tmp:
        content_dir = Path(tmp)
        articles_dir = content_dir / "articles"
        articles_dir.mkdir()
        (articles_dir / "change-management-at-the-messy-start.md").write_text(
            """---
title: Change Management at the Messy Start
domain: change_management
type: article
tags:
- early_change
- stakeholder_narratives
- sensemaking
status: published
---

# Change Management at the Messy Start

- "This will be dumped on us."
- "The decision has already been made."
- "They'll ask for input, then ignore it."
""",
            encoding="utf-8",
        )
        fixture_docs = load_corpus_chunks(content_dir)
        require(fixture_docs, "frontmatter fixture was not loaded")
        metadata = fixture_docs[0]["metadata"]
        require(metadata["title"] == "Change Management at the Messy Start",
                "fixture title was not parsed")
        require(metadata["domain"] == "change_mgmt",
                "frontmatter domain alias was not normalized")
        require(metadata["type"] == "article", "fixture type was not parsed")
        require("stakeholder_narratives" in metadata["tags"], "fixture tags were not parsed")
        require(metadata["status"] == "published", "fixture status was not parsed")

    print(f"OK: loaded {len(docs)} chunks across domains: {sorted(domains)}")


if __name__ == "__main__":
    main()
