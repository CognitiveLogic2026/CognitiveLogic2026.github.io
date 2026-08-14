"""Governed deterministic retrieval for informational sources.

This module never imports or mutates the QEN decision engine. Registry documents
are evidence for citation only, not configuration or decision authority.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
REGISTRY_PATH = BASE_DIR / "data" / "source-registry.json"
INDEX_PATH = BASE_DIR / "data" / "source-index.json"
INDEX_SCHEMA_VERSION = "1.0"

# Query anchors are deliberately kept outside the governed registry: they tune
# retrieval only and do not alter source metadata or the evidence model.
_SOURCE_SCOPES = {
    "dfv 002": {"DFV-002"},
    "hva 001": {"CASE-HVA-001"},
    "coste360": {"CASE-COSTE360-001", "EA-009"},
    "egea": {"CASE-EGEA-QEN-001", "BEN-EGEA-QEN-001"},
    "agcm": {"CASE-AGCM-001", "AGCM-AS1930-NOTE-001"},
    "ea 009": {"EA-009", "CASE-COSTE360-001"},
    "cs 010": {"CS-010", "CASE-COASTAL-001"},
}

REQUIRED_FIELDS = {
    "source_id", "title", "version", "source_path", "canonical_url",
    "category", "authority", "date", "status", "source_class",
    "confidence", "scope", "language", "search_terms", "allowed_use",
    "prohibited_use", "publication_status", "enabled", "sha256",
}
PROTECTED_PROHIBITIONS = {"modify_qen_configuration", "modify_qen_decisions"}
CONFIDENCE_VALUES = {"low", "medium", "high"}
SOURCE_CLASSES = {"primary", "secondary"}
CASE_TYPES = set("ABCDEFG")
EVIDENCE_LABELS = {
    "PUBLIC EVIDENCE", "PRIMARY SOURCE", "ASSESSMENT INFERENCE",
    "NOT VERIFIABLE", "HUMAN DECISION REQUIRED",
}
CASE_REQUIRED_FIELDS = {
    "document_type", "primary_case_type", "relationship_with_cognitive_logic",
    "observed_organisation", "sector", "jurisdiction", "publication_date",
    "last_verified_at", "primary_sources", "provenance", "evidence_labels",
    "limitations", "uncertainty", "final_human_authority",
}


class RegistryError(ValueError):
    """The governed source registry or one of its sources is invalid."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.lower())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", value))


def load_registry(path: Path = REGISTRY_PATH, *, verify_sources: bool = True) -> dict[str, Any]:
    registry = json.loads(path.read_text(encoding="utf-8"))
    if registry.get("allowlist_enforced") is not True:
        raise RegistryError("Source allowlist must be explicitly enforced")
    if not registry.get("registry_version") or not isinstance(registry.get("sources"), list):
        raise RegistryError("Registry version and sources are required")
    allowed_categories = set(registry.get("allowed_categories", []))

    seen: set[str] = set()
    for source in registry["sources"]:
        missing = REQUIRED_FIELDS - source.keys()
        if missing:
            raise RegistryError(f"Missing fields for source: {sorted(missing)}")
        if source["source_id"] in seen:
            raise RegistryError(f"Duplicate source_id: {source['source_id']}")
        seen.add(source["source_id"])
        if source["source_class"] not in SOURCE_CLASSES:
            raise RegistryError(f"Invalid source_class: {source['source_id']}")
        if source["confidence"] not in CONFIDENCE_VALUES:
            raise RegistryError(f"Invalid confidence: {source['source_id']}")
        if source["category"] not in allowed_categories:
            raise RegistryError(f"Invalid category: {source['source_id']}")
        if source.get("document_type") == "case_study":
            missing_case = CASE_REQUIRED_FIELDS - source.keys()
            if missing_case:
                raise RegistryError(
                    f"Missing governed case fields for {source['source_id']}: {sorted(missing_case)}"
                )
            if source["primary_case_type"] not in CASE_TYPES:
                raise RegistryError(f"Invalid primary_case_type: {source['source_id']}")
            if not EVIDENCE_LABELS.issubset(set(source["evidence_labels"])):
                raise RegistryError(f"Evidence boundary missing: {source['source_id']}")
        if not PROTECTED_PROHIBITIONS.issubset(set(source["prohibited_use"])):
            raise RegistryError(f"Decision boundary missing: {source['source_id']}")
        source_path = (BASE_DIR / source["source_path"]).resolve()
        if BASE_DIR not in source_path.parents:
            raise RegistryError(f"Source path escapes repository: {source['source_id']}")
        if verify_sources and source["enabled"]:
            if not source_path.is_file():
                raise RegistryError(f"Missing allowlisted source: {source['source_id']}")
            if _sha256(source_path) != source["sha256"]:
                raise RegistryError(f"Checksum mismatch: {source['source_id']}")
    return registry


def _sections(markdown: str) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    heading = "Document"
    lines: list[str] = []
    for line in markdown.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if match:
            if lines:
                text = "\n".join(lines).strip()
                if text:
                    sections.append({"section": heading, "text": text})
            heading = match.group(1).strip()
            lines = []
        else:
            lines.append(line)
    text = "\n".join(lines).strip()
    if text:
        sections.append({"section": heading, "text": text})
    return sections


def build_index(
    registry_path: Path = REGISTRY_PATH,
    destination: Path = INDEX_PATH,
) -> dict[str, Any]:
    registry = load_registry(registry_path)
    documents: list[dict[str, Any]] = []
    for source in registry["sources"]:
        if not source["enabled"]:
            continue
        path = (BASE_DIR / source["source_path"]).resolve()
        markdown = path.read_text(encoding="utf-8")
        entries = _sections(markdown) or [{"section": "Document", "text": markdown}]
        documents.append({
            "source_id": source["source_id"],
            "source_sha256": source["sha256"],
            "metadata": {
                key: source[key] for key in (
                    "title", "version", "canonical_url", "category", "authority",
                    "date", "status", "source_class", "confidence", "scope",
                    "language", "publication_status",
                )
            } | {
                key: source[key] for key in (
                    "document_type", "primary_case_type", "relationship_with_cognitive_logic",
                    "observed_organisation", "sector", "jurisdiction", "publication_date",
                    "last_verified_at", "primary_sources", "provenance", "evidence_labels",
                    "limitations", "uncertainty", "final_human_authority",
                ) if key in source
            },
            "search_terms": source["search_terms"],
            "warnings": source.get("warnings", []),
            "sections": entries,
        })
    core = {
        "schema_version": INDEX_SCHEMA_VERSION,
        "registry_version": registry["registry_version"],
        "registry_hash": _stable_hash(registry),
        "documents": documents,
    }
    core["index_version"] = _stable_hash(core)
    destination.write_text(
        json.dumps(core, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return core


def load_index(
    registry_path: Path = REGISTRY_PATH,
    index_path: Path = INDEX_PATH,
) -> tuple[dict[str, Any] | None, str]:
    try:
        registry = load_registry(registry_path)
    except (OSError, json.JSONDecodeError, RegistryError):
        return None, "registry_error"
    if not index_path.is_file():
        return None, "index_missing"
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "index_invalid"
    if index.get("registry_hash") != _stable_hash(registry):
        return None, "index_stale"
    if index.get("schema_version") != INDEX_SCHEMA_VERSION:
        return None, "index_incompatible"
    return index, "ready"


def knowledge_version() -> dict[str, str | None]:
    index, status = load_index()
    registry_version = None
    try:
        registry_version = load_registry(verify_sources=False).get("registry_version")
    except (OSError, json.JSONDecodeError, RegistryError):
        pass
    return {
        "registry_version": registry_version,
        "index_version": index.get("index_version") if index else None,
        "retrieval_status": status,
    }


def retrieve(query: str, *, limit: int = 5, minimum_score: float = 0.25) -> dict[str, Any]:
    index, status = load_index()
    version = knowledge_version()
    if not index:
        return {"sources": [], "uncertainty": "Retrieval unavailable: " + status,
                "confidence": "low", "retrieval_status": status,
                "knowledge_version": version}

    normalized = normalize_text(query)
    query_terms = set(normalized.split())
    if not query_terms:
        return {"sources": [], "uncertainty": "No searchable query terms.",
                "confidence": "low", "retrieval_status": "no_results",
                "knowledge_version": version}

    scoped_ids = set().union(*(
        source_ids for anchor, source_ids in _SOURCE_SCOPES.items()
        if re.search(rf"(?<![a-z0-9]){re.escape(anchor)}(?![a-z0-9])", normalized)
    ))

    matches: list[dict[str, Any]] = []
    for document in index["documents"]:
        meta = document["metadata"]
        source_id = document["source_id"]
        # An explicit governed identifier defines the documentary perimeter.
        # Related records are already included in the scope map (for example a
        # case page and its evidence catalogue); unrelated cases cannot enter
        # merely through generic words such as evidence, limits or governance.
        if scoped_ids and source_id not in scoped_ids:
            continue
        title_terms = set(normalize_text(meta["title"]).split())
        tag_terms = set(normalize_text(" ".join(document["search_terms"])).split())
        metadata_terms = set(normalize_text(" ".join(str(v) for v in meta.values())).split())
        for section in document["sections"]:
            section_heading = normalize_text(section["section"])
            section_terms = set(section_heading.split())
            content_terms = set(normalize_text(section["text"]).split())
            title_hits = len(query_terms & title_terms)
            tag_hits = len(query_terms & tag_terms)
            metadata_hits = len(query_terms & metadata_terms)
            section_hits = len(query_terms & section_terms)
            content_hits = len(query_terms & content_terms)
            phrase_bonus = 2 if normalized and normalized in normalize_text(section["text"]) else 0
            heading_bonus = 3 if normalized and normalized in section_heading else 0
            authority_bonus = 0.35 if meta["source_class"] == "primary" else 0.0
            official_bonus = 0.2 if "AGCM" in meta["authority"] else 0.0
            raw = title_hits * 4 + tag_hits * 3 + section_hits * 3 + metadata_hits + content_hits + phrase_bonus + heading_bonus
            if raw == 0:
                continue
            exact_source = bool(re.search(
                rf"(?<![a-z0-9]){re.escape(normalize_text(source_id))}(?![a-z0-9])",
                normalized,
            ))
            exact_title = normalize_text(meta["title"]) in normalized
            exact_term = any(
                len(term := normalize_text(value)) >= 4 and term in normalized
                for value in document["search_terms"]
            )
            exact_bonus = (
                0.9 if exact_source else 0.55 if exact_title
                else 0.35 if exact_term else 0.0
            )
            scope_adjustment = 0.65 if scoped_ids else 0.0
            rank_score = (
                raw / max(6, len(query_terms) * 4)
                + authority_bonus + official_bonus + exact_bonus + scope_adjustment
            )
            score = min(1.0, rank_score)
            if score < minimum_score:
                continue
            excerpt = re.sub(r"\s+", " ", section["text"]).strip()[:360]
            matches.append({
                "source_id": document["source_id"], "title": meta["title"],
                "canonical_url": meta["canonical_url"], "category": meta["category"],
                "authority": meta["authority"], "author": meta["authority"], "date": meta["date"],
                "source_class": meta["source_class"], "confidence": meta["confidence"],
                "section": section["section"], "excerpt": excerpt,
                "relevance_score": round(score, 3), "_rank_score": rank_score,
                "warnings": document["warnings"],
                "evidence_labels": meta.get("evidence_labels", []),
                "limitations": meta.get("limitations", ""),
                "source_uncertainty": meta.get("uncertainty", ""),
                "final_human_authority": meta.get("final_human_authority", ""),
                "primary_sources": meta.get("primary_sources", []),
            })

    matches.sort(key=lambda item: (
        -item["_rank_score"], item["source_class"] != "primary",
        item["source_id"], item["section"],
    ))
    deduplicated: list[dict[str, Any]] = []
    seen: set[str] = set()
    for match in matches:
        if match["source_id"] in seen:
            continue
        seen.add(match["source_id"])
        match.pop("_rank_score", None)
        deduplicated.append(match)
        if len(deduplicated) >= max(1, min(limit, 10)):
            break

    if not deduplicated:
        return {"sources": [], "uncertainty": "No registered source met the relevance threshold.",
                "confidence": "low", "retrieval_status": "no_results",
                "knowledge_version": version}
    confidence = "high" if any(m["source_class"] == "primary" and m["relevance_score"] >= 0.7 for m in deduplicated) else "medium"
    uncertainty = (
        "Review source date, status and warnings; this response is not legal advice."
        if any(m["warnings"] for m in deduplicated)
        else "Source-backed informational retrieval; this response is not legal advice."
    )
    return {"sources": deduplicated, "uncertainty": uncertainty,
            "confidence": confidence, "retrieval_status": "ready",
            "knowledge_version": version}
