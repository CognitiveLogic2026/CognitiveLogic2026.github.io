"""QEN Sovereign Intelligence Engine — ADR-CLE-004."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GRAPH_PATH = Path(__file__).with_name("graph.json")
ENGINE_VERSION = "qen-sovereign-1.0"

RISK_RULES = {
    "PROHIBITED": {
        "keywords": (
            "social scoring",
            "manipolazione subliminale",
            "subliminal manipulation",
            "sfruttamento vulnerabilità",
            "real-time biometric identification",
            "identificazione biometrica remota in tempo reale",
        ),
        "score": 0.95,
        "annex": "Article 5",
    },
    "HIGH": {
        "keywords": (
            "biometr",
            "recruitment",
            "selezione personale",
            "selezione del personale",
            "filtra i cv",
            "filtro cv",
            "screening cv",
            "curriculum",
            "candidati",
            "credito",
            "credit scoring",
            "migrazione",
            "law enforcement",
            "infrastruttura critica",
            "istruzione",
            "accesso servizi essenziali",
        ),
        "score": 0.75,
        "annex": "III",
    },
    "MEDIUM": {
        "keywords": (
            "chatbot",
            "generative ai",
            "deepfake",
            "emotion recognition",
            "riconoscimento emozioni",
            "raccomandazione automatizzata",
        ),
        "score": 0.45,
        "annex": "Transparency",
    },
}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def qen_score(vs: float, va: float, vt: float) -> float:
    values = [float(vs), float(va), float(vt)]
    if max(values) <= 10:
        values = [v * 10 for v in values]
    values = [max(0.0, min(100.0, v)) for v in values]
    return round(values[0] * 0.40 + values[1] * 0.35 + values[2] * 0.25, 2)


def _graph_context(query: str) -> list[dict[str, Any]]:
    if not GRAPH_PATH.exists():
        return []

    try:
        graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []

    terms = {
        term
        for term in re.findall(r"[a-zà-ÿ0-9_]+", query.lower())
        if len(term) >= 4
    }

    matches: list[tuple[int, dict[str, Any]]] = []
    for node in graph.get("nodes", {}).values():
        text = json.dumps(node, ensure_ascii=False).lower()
        relevance = sum(1 for term in terms if term in text)
        if relevance:
            matches.append((relevance, node))

    matches.sort(key=lambda item: item[0], reverse=True)
    return [node for _, node in matches[:8]]


def classify_risk(
    description: str,
    context: str = "",
    sector: str = "",
) -> dict[str, Any]:
    text = " ".join((description, context, sector)).lower()

    level = "LOW"
    risk_score = 0.15
    annex = "None"

    for candidate in ("PROHIBITED", "HIGH", "MEDIUM"):
        rule = RISK_RULES[candidate]
        if any(keyword in text for keyword in rule["keywords"]):
            level = candidate
            risk_score = rule["score"]
            annex = rule["annex"]
            break

    personal_data = any(
        keyword in text
        for keyword in (
            "dati personali",
            "personal data",
            "profilazione",
            "profiling",
            "biometr",
            "geolocal",
        )
    )
    automated_decision = any(
        keyword in text
        for keyword in (
            "decisione automat",
            "automated decision",
            "selezione automat",
            "automated selection",
            "credit scoring",
            "selezione personale",
            "recruitment",
        )
    )

    gdpr_risk = (
        "HIGH"
        if personal_data and automated_decision
        else "MEDIUM"
        if personal_data
        else "LOW"
    )

    gaps = []
    recommendations = []

    if level in {"PROHIBITED", "HIGH"}:
        gaps.extend(["risk_management", "human_oversight", "technical_documentation"])
        recommendations.extend([
            "Documentare finalità, contesto d'uso e soggetti coinvolti",
            "Attivare supervisione umana e registrazione degli eventi",
            "Eseguire valutazione normativa e test prima della messa in servizio",
        ])
    elif level == "MEDIUM":
        gaps.append("transparency_notice")
        recommendations.append(
            "Informare chiaramente gli utenti dell'interazione con un sistema AI"
        )

    if personal_data:
        gaps.append("gdpr_legal_basis")
        recommendations.append(
            "Verificare base giuridica, minimizzazione e tempi di conservazione"
        )

    if automated_decision:
        gaps.append("gdpr_article_22_review")
        recommendations.append(
            "Garantire intervento umano, contestazione e spiegazione della decisione"
        )

    vs = {
        "PROHIBITED": 20,
        "HIGH": 45,
        "MEDIUM": 70,
        "LOW": 88,
    }[level]
    va = 45 if automated_decision else 72
    vt = 55 if personal_data else 80
    qscore = qen_score(vs, va, vt)

    evidence = _graph_context(text)
    decision_id = hashlib.sha256(
        f"{text}|{_utcnow()}".encode("utf-8")
    ).hexdigest()[:16]

    return {
        "decision_id": decision_id,
        "engine": "QEN Sovereign Intelligence Engine",
        "architecture": "ADR-CLE-004",
        "timestamp": _utcnow(),
        "risk_level": level,
        "risk_score": risk_score,
        "eu_classification": f"{level} - {annex}",
        "gdpr_risk": gdpr_risk,
        "qen_score": qscore,
        "vs": vs,
        "va": va,
        "vt": vt,
        "gaps": sorted(set(gaps)),
        "recommendations": list(dict.fromkeys(recommendations)),
        "decision": level,
        "summary": (
            "Classificazione prodotta mediante regole QEN deterministiche, "
            "Knowledge Graph ed evidenze intelligibili."
        ),
        "knowledge_evidence": [
            {
                "id": node.get("id"),
                "type": node.get("type"),
                "label": node.get("label"),
                "evide_id": node.get("evide_id"),
            }
            for node in evidence
        ],
    }


def score_entity(
    name: str,
    description: str,
    sector: str = "",
    vs: float | None = None,
    va: float | None = None,
    vt: float | None = None,
) -> dict[str, Any]:
    if vs is None or va is None or vt is None:
        risk = classify_risk(description, sector=sector)
        vs = risk["vs"]
        va = risk["va"]
        vt = risk["vt"]

    score = qen_score(vs, va, vt)

    if score >= 85:
        badge = "QEN DIAMANTE"
    elif score >= 75:
        badge = "QEN ORO"
    elif score >= 65:
        badge = "QEN ARGENTO"
    elif score >= 60:
        badge = "QEN BRONZO"
    else:
        badge = "QEN IN SVILUPPO"

    return {
        "entity_name": name,
        "sector": sector,
        "qen_score": score,
        "badge": badge,
        "vs": float(vs),
        "va": float(va),
        "vt": float(vt),
        "provider": "qen-sovereign",
        "confidence": "HIGH" if all(v is not None for v in (vs, va, vt)) else "LOW",
        "timestamp": _utcnow(),
        "summary": "Scoring deterministico QEN basato su dati intelligibili.",
    }



def compliance_audit(
    entity_name: str,
    description: str,
    sector: str = "",
) -> dict[str, Any]:
    risk = classify_risk(description, sector=sector)

    return {
        **risk,
        "entity_name": entity_name,
        "provider": "qen-sovereign",
        "eu_ai_act": {
            "allegato": risk["eu_classification"],
            "livello_rischio": risk["risk_level"],
            "motivazione": risk["summary"],
        },
        "gdpr": {
            "risk": risk["gdpr_risk"],
            "dpia_required": risk["gdpr_risk"] == "HIGH",
            "articoli": (
                ["Art. 22", "Art. 35"]
                if risk["gdpr_risk"] == "HIGH"
                else ["Art. 5", "Art. 6"]
                if risk["gdpr_risk"] == "MEDIUM"
                else []
            ),
        },
        "remediation": risk["recommendations"],
    }


def territorial_map(
    entity_name: str,
    description: str,
    location: str = "",
    places_context: str = "",
) -> dict[str, Any]:
    text = " ".join((description, location, places_context)).lower()

    local_signals = (
        "locale", "territorio", "km0", "km 0", "filiera corta",
        "produttori", "artigiani", "cooperativa", "de.co", "comunità",
    )
    signals = sum(1 for keyword in local_signals if keyword in text)
    vt_score = min(95.0, 55.0 + signals * 5.0)

    stakeholders = []
    for line in places_context.splitlines():
        line = line.strip()
        if line.startswith("- "):
            stakeholders.append(line[2:])

    return {
        "decision_id": hashlib.sha256(
            f"territorial|{entity_name}|{description}|{location}|{_utcnow()}".encode()
        ).hexdigest()[:16],
        "engine": "QEN Sovereign Intelligence Engine",
        "architecture": "ADR-CLE-004",
        "provider": "qen-sovereign",
        "timestamp": _utcnow(),
        "entity_name": entity_name,
        "location": location,
        "vt_score": vt_score,
        "stakeholders": stakeholders[:10],
        "supply_chain": {
            "local_pct": min(100.0, signals * 12.5),
            "avg_distance_km": None,
            "certifications": [],
        },
        "territorial_impact": (
            "ALTO" if vt_score >= 80 else
            "MEDIO" if vt_score >= 65 else
            "DA_VERIFICARE"
        ),
        "recommendations": [
            "Documentare fornitori, distanze e provenienza delle materie prime",
            "Mappare stakeholder, occupazione e partnership territoriali",
            "Associare evidenze verificabili agli indicatori territoriali",
        ],
        "summary": (
            "Mappatura deterministica prodotta da indicatori territoriali "
            "QEN e fonti dati intelligibili."
        ),
        "knowledge_evidence": _graph_context(text),
    }


def advisory_assessment(
    entity_name: str,
    description: str,
    sector: str = "",
    risk_level: str = "",
) -> dict[str, Any]:
    risk = classify_risk(
        description,
        context=risk_level,
        sector=sector,
    )

    priority_actions = list(risk["recommendations"])
    if sector.lower() in {"balneare", "turismo", "horeca"}:
        priority_actions.append(
            "Verificare concessioni, autorizzazioni e obblighi settoriali applicabili"
        )

    return {
        "decision_id": risk["decision_id"],
        "engine": risk["engine"],
        "architecture": risk["architecture"],
        "provider": "qen-sovereign",
        "timestamp": risk["timestamp"],
        "entity_name": entity_name,
        "priority_actions": list(dict.fromkeys(priority_actions)),
        "compliance_timeline": [
            {
                "priority": "IMMEDIATA",
                "action": action,
            }
            for action in priority_actions[:3]
        ],
        "regulatory_refs": [
            risk["eu_classification"],
            "GDPR Art. 22" if risk["gdpr_risk"] == "HIGH" else "GDPR",
            "ADR-CLE-004",
        ],
        "cost_estimate": "DA_DEFINIRE_SU_EVIDENZE",
        "risk_level": risk["risk_level"],
        "qen_score": risk["qen_score"],
        "summary": (
            "Percorso advisory generato dal QEN Sovereign Intelligence Engine "
            "mediante regole, Knowledge Graph ed evidenze intelligibili."
        ),
        "knowledge_evidence": risk["knowledge_evidence"],
    }
