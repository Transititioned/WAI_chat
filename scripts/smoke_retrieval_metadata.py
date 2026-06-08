from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.loaders import load_corpus_chunks
from app.retrieval_policy import detect_retrieval_intent, rank_retrieval_candidates
from app.router import route_info



def require(condition, message):
    if not condition:
        raise AssertionError(message)


def first_doc_by_source(docs, source):
    for doc in docs:
        if doc["metadata"].get("source") == source:
            return doc
    raise AssertionError(f"expected source not loaded: {source}")


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

    source_query = 'from the article "Change Management at the Messy Start", summarise the main points'
    advisory_query = (
        "The business keeps asking for training. My instinct is that's not actually "
        "the problem. What are the possible root causes?"
    )
    require(detect_retrieval_intent(source_query) == "source_lookup",
            "source lookup intent was not detected")
    require(detect_retrieval_intent(advisory_query) == "advisory",
            "advisory intent was not detected")

    exact_article = {
        "content": "Article chunk",
        "metadata": {
            "title": "Change Management at the Messy Start",
            "source_path": "articles/change-management-at-the-messy-start.md",
            "source": "change-management-at-the-messy-start.md",
            "type": "article",
            "doc_type": "article",
            "chunk_index": 0,
        },
    }
    trigger_card = {
        "content": "Trigger/action card chunk",
        "metadata": {
            "title": "Training Request May Hide Process Uncertainty",
            "source_path": "wai_change_mgmt_library/cards/card_training_request_may_hide_process_uncertainty.md",
            "source": "card_training_request_may_hide_process_uncertainty.md",
            "type": "change_pattern",
            "doc_type": "change_pattern",
            "chunk_index": 0,
        },
    }
    source_ranked = rank_retrieval_candidates(
        [
            {"doc": trigger_card, "origin": "semantic", "score": 0},
            {"doc": exact_article, "origin": "exact", "score": 0},
        ],
        intent="source_lookup",
    )
    require(source_ranked[0]["metadata"]["source"] == "change-management-at-the-messy-start.md",
            "source lookup ranking did not keep exact source first")

    advisory_ranked = rank_retrieval_candidates(
        [
            {"doc": exact_article, "origin": "exact", "score": 0},
            {"doc": trigger_card, "origin": "semantic", "score": 0},
        ],
        intent="advisory",
    )
    require(advisory_ranked[0]["metadata"]["source"] == "card_training_request_may_hide_process_uncertainty.md",
            "advisory ranking did not prefer trigger/action cards")

    messy_article = first_doc_by_source(docs, "change-management-at-the-messy-start.md")
    training_card = first_doc_by_source(docs, "card_training_request_may_hide_process_uncertainty.md")
    resistance_card = first_doc_by_source(docs, "card_resistance_as_project_memory.md")
    silence_card = first_doc_by_source(docs, "card_silence_is_not_agreement.md")
    trust_card = first_doc_by_source(docs, "card_stakeholder_trust_bank.md")
    ranked_training = rank_retrieval_candidates(
        [
            {"doc": messy_article, "origin": "exact", "score": 0},
            {"doc": training_card, "origin": "semantic", "score": 0},
            {"doc": resistance_card, "origin": "semantic", "score": 0},
            {"doc": silence_card, "origin": "semantic", "score": 0},
            {"doc": trust_card, "origin": "semantic", "score": 0},
        ],
        intent="advisory",
        limit=4,
    )
    ranked_training_sources = [doc["metadata"]["source"] for doc in ranked_training]
    require(ranked_training_sources[:3] == [
        "card_training_request_may_hide_process_uncertainty.md",
        "card_resistance_as_project_memory.md",
        "card_silence_is_not_agreement.md",
    ], f"training/scepticism advisory ranking wrong: {ranked_training_sources}")

    constraint_card = first_doc_by_source(docs, "card_constraint_tradeoff_timeline.md")
    push_card = first_doc_by_source(docs, "card_push_without_alienating.md")
    surprises_card = first_doc_by_source(docs, "card_no_surprises_before_governance.md")
    ranked_timeline = rank_retrieval_candidates(
        [
            {"doc": messy_article, "origin": "exact", "score": 0},
            {"doc": constraint_card, "origin": "semantic", "score": 0},
            {"doc": push_card, "origin": "semantic", "score": 0},
            {"doc": surprises_card, "origin": "semantic", "score": 0},
        ],
        intent="advisory",
        limit=3,
    )
    ranked_timeline_sources = [doc["metadata"]["source"] for doc in ranked_timeline]
    require(ranked_timeline_sources == [
        "card_constraint_tradeoff_timeline.md",
        "card_push_without_alienating.md",
        "card_no_surprises_before_governance.md",
    ], f"timeline advisory ranking wrong: {ranked_timeline_sources}")

    readiness_card = first_doc_by_source(docs, "card_operational_readiness_gut_check.md")
    readiness_loop_card = first_doc_by_source(docs, "card_change_readiness_loop.md")
    role_card = first_doc_by_source(docs, "card_change_role_trifecta.md")
    ranked_readiness = rank_retrieval_candidates(
        [
            {"doc": messy_article, "origin": "exact", "score": 0},
            {"doc": readiness_card, "origin": "semantic", "score": 0},
            {"doc": readiness_loop_card, "origin": "semantic", "score": 0},
            {"doc": role_card, "origin": "semantic", "score": 0},
        ],
        intent="advisory",
        limit=3,
    )
    ranked_readiness_sources = [doc["metadata"]["source"] for doc in ranked_readiness]
    require(ranked_readiness_sources == [
        "card_operational_readiness_gut_check.md",
        "card_change_readiness_loop.md",
        "card_change_role_trifecta.md",
    ], f"readiness advisory ranking wrong: {ranked_readiness_sources}")

    print(f"OK: loaded {len(docs)} chunks across domains: {sorted(domains)}")


if __name__ == "__main__":
    main()
