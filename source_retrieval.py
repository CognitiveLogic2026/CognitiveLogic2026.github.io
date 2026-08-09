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

REQUIRED_FIELDS = {
    "source_id", "title", "version", "source_path", "canonical_url",
    "category", "authority", "date", "status", "source_class",
    "confidence", "scope", "language", "search_terms", "allowed_use",
    "prohibited_use", "publication_status", "enabled", "sha256",
}
PROTECTED_PROHIBITIONS = {"modify_qen_configuration", "modify_qen_decisions"}
CONFIDENCE_VALUES = {"low", "medium", "high"}
SOURCE_CLASSES = {"primary", "secondary"}


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


def retrieve(query: str, *, limit: int = 5, minimum_score: float = 0.18) -> dict[str, Any]:
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

    matches: list[dict[str, Any]] = []
    for document in index["documents"]:
        meta = document["metadata"]
        title_terms = set(normalize_text(meta["title"]).split())
        tag_terms = set(normalize_text(" ".join(document["search_terms"])).split())
        metadata_terms = set(normalize_text(" ".join(str(v) for v in meta.values())).split())
        for section in document["sections"]:
            content_terms = set(normalize_text(section["text"]).split())
            title_hits = len(query_terms & title_terms)
            tag_hits = len(query_terms & tag_terms)
            metadata_hits = len(query_terms & metadata_terms)
            content_hits = len(query_terms & content_terms)
            phrase_bonus = 2 if normalized and normalized in normalize_text(section["text"]) else 0
            authority_bonus = 0.35 if meta["source_class"] == "primary" else 0.0
            official_bonus = 0.2 if "AGCM" in meta["authority"] else 0.0
            raw = title_hits * 4 + tag_hits * 3 + metadata_hits + content_hits + phrase_bonus
            if raw == 0:
                continue
            score = min(1.0, (raw / max(6, len(query_terms) * 4)) + authority_bonus + official_bonus)
            if score < minimum_score:
                continue
            excerpt = re.sub(r"\s+", " ", section["text"]).strip()[:360]
            matches.append({
                "source_id": document["source_id"], "title": meta["title"],
                "canonical_url": meta["canonical_url"], "category": meta["category"],
                "authority": meta["authority"], "date": meta["date"],
                "source_class": meta["source_class"], "confidence": meta["confidence"],
                "section": section["section"], "excerpt": excerpt,
                "relevance_score": round(score, 3), "warnings": document["warnings"],
            })

    matches.sort(key=lambda item: (
        -item["relevance_score"], item["source_class"] != "primary",
        item["source_id"], item["section"],
    ))
    deduplicated: list[dict[str, Any]] = []
    seen: set[str] = set()
    for match in matches:
        if match["source_id"] in seen:
            continue
        seen.add(match["source_id"])
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
