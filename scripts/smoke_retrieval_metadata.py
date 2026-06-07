from pathlib import Path
import sys

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

    print(f"OK: loaded {len(docs)} chunks across domains: {sorted(domains)}")


if __name__ == "__main__":
    main()
