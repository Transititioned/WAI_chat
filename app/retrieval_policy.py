import re
from pathlib import Path


SOURCE_LOOKUP_TERMS = [
    "summarise",
    "summarize",
    "summary",
    "what does",
    "what did",
    "quote",
    "show me",
    "show the source",
    "inspect",
    "from the article",
    "from source",
    "main points",
    "key points",
    "list the examples",
]

ADVISORY_TERMS = [
    "what should i do",
    "what should we do",
    "how should i",
    "how should we",
    "how do i",
    "how do we",
    "root cause",
    "root causes",
    "what pattern",
    "what am i seeing",
    "what are we seeing",
    "what is going on",
    "handle this",
    "frame it",
    "keeps asking",
    "users are",
    "business is",
    "business keeps",
    "sponsor wants",
    "participation is weak",
    "not actually the problem",
]

LOW_PRIORITY_PATH_PARTS = [
    "source_full",
    "index",
    "indexes",
    "_staging",
    "/staging/",
]

STAKEHOLDER_CARD_PATH = "wai_change_mgmt_library/stakeholder_engagement/cards/"
STAKEHOLDER_EXAMPLE_PATH = "wai_change_mgmt_library/stakeholder_engagement/examples/"


def normalize_text(value: str) -> str:
    value = value or ""
    value = value.lower()
    value = re.sub(r"[_\-]+", " ", value)
    value = re.sub(r"[^a-z0-9\s]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def detect_retrieval_intent(query: str) -> str:
    q = normalize_text(query)
    if any(term in q for term in ADVISORY_TERMS):
        return "advisory"
    if any(term in q for term in SOURCE_LOOKUP_TERMS):
        return "source_lookup"
    if "?" in query:
        return "advisory"
    return "advisory"


def metadata_for(doc) -> dict:
    return doc["metadata"] if isinstance(doc, dict) else doc.metadata


def source_key(metadata: dict) -> str:
    return metadata.get("source_path") or metadata.get("source_filename") or metadata.get("source", "")


def metadata_key(doc) -> tuple:
    metadata = metadata_for(doc)
    return metadata.get("source_path"), metadata.get("chunk_index")


def content_type_adjustment(metadata: dict, intent: str):
    doc_type = (metadata.get("type") or metadata.get("doc_type") or "").lower()
    source_path = (metadata.get("source_path") or metadata.get("source") or "").lower()
    filename = Path(source_path).name.lower()
    reasons = []
    score = 0

    if any(part in source_path for part in LOW_PRIORITY_PATH_PARTS):
        reasons.append("downrank_low_priority_path")
        score -= 100

    if intent == "source_lookup":
        if doc_type == "article" or "/articles/" in f"/{source_path}":
            reasons.append("source_lookup_article")
            score += 40
        if filename.startswith("card_") or doc_type in {"change_pattern", "card", "pm_toolkit"}:
            reasons.append("source_lookup_card_support")
            score += 25
        if doc_type == "example" or "/examples/" in f"/{source_path}":
            reasons.append("source_lookup_example_support")
            score += 20
        if not reasons:
            reasons.append("source_lookup_default")
            score += 10
        return score, reasons

    if doc_type == "change_pattern":
        reasons.append("boost_type_change_pattern")
        score += 120
    if STAKEHOLDER_CARD_PATH in source_path:
        reasons.append("boost_stakeholder_engagement_card_path")
        score += 80
    if filename.startswith("card_") or doc_type in {"card", "pm_toolkit"}:
        reasons.append("boost_card_filename_or_type")
        score += 60
    if doc_type == "applied_example":
        reasons.append("boost_type_applied_example")
        score += 70
    if STAKEHOLDER_EXAMPLE_PATH in source_path:
        reasons.append("boost_stakeholder_engagement_example_path")
        score += 50
    if doc_type == "example" or "/examples/" in f"/{source_path}":
        reasons.append("boost_example")
        score += 45
    if doc_type == "article" or "/articles/" in f"/{source_path}":
        reasons.append("downrank_article_for_advisory")
        score -= 10
    if not reasons:
        reasons.append("default_advisory")
        score += 10

    return score, reasons


def rank_retrieval_candidates(candidates: list, intent: str, limit: int = 5, return_details: bool = False):
    best_by_key = {}

    for candidate in candidates:
        doc = candidate["doc"]
        key = metadata_key(doc)

        metadata = metadata_for(doc)
        raw_score = candidate.get("score", 0)
        adjusted_score = raw_score
        reasons = []
        type_adjustment, type_reasons = content_type_adjustment(metadata, intent)
        adjusted_score += type_adjustment
        reasons.extend(type_reasons)

        if candidate.get("origin") == "exact":
            if intent == "source_lookup":
                adjusted_score += 45
                reasons.append("boost_exact_source_lookup")
            else:
                adjusted_score += 3
                reasons.append("minor_exact_support_advisory")
        elif candidate.get("origin") == "metadata":
            adjusted_score += 20
            reasons.append("boost_metadata_match")
        elif candidate.get("origin") == "semantic":
            adjusted_score += 10
            reasons.append("boost_semantic_match")

        candidate["raw_score"] = raw_score
        candidate["adjusted_score"] = adjusted_score
        candidate["rank_reasons"] = reasons
        if key not in best_by_key or adjusted_score > best_by_key[key]["adjusted_score"]:
            best_by_key[key] = candidate

    ranked = [(candidate["adjusted_score"], candidate) for candidate in best_by_key.values()]
    ranked.sort(
        key=lambda item: (
            item[0],
            -metadata_for(item[1]["doc"]).get("chunk_index", 0),
        ),
        reverse=True,
    )

    selected = [candidate for _, candidate in ranked[:limit]]
    if return_details:
        return selected
    return [candidate["doc"] for candidate in selected]
