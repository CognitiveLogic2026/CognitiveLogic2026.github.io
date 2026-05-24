import os
import json
import re
from datetime import datetime

import anthropic
import json_repair
import requests as _requests
from flask import request, jsonify

_client = None


def _places_enrich(location: str) -> str:
    """Return a text block with real local suppliers from Google Places, or ''."""
    import sys
    key = os.getenv("GOOGLE_PLACES_API_KEY", "")
    if not key or not location:
        print(f"[Places] skip: key={'set' if key else 'EMPTY'} location={location!r}", file=sys.stderr)
        return ""

    queries = [
        f"produttori agricoli locali {location}",
        f"cooperativa alimentare {location}",
    ]
    found = []
    for q in queries:
        try:
            resp = _requests.post(
                "https://places.googleapis.com/v1/places:searchText",
                headers={
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": key,
                    "X-Goog-FieldMask": "places.displayName,places.formattedAddress",
                },
                json={"textQuery": q},
                timeout=5,
            ).json()
            hits = resp.get("places", [])
            print(f"[Places] query={q!r} → {len(hits)} results", file=sys.stderr)
            for p in hits[:4]:
                name = p.get("displayName", {}).get("text", "")
                addr = p.get("formattedAddress", "")
                found.append(f"- {name} ({addr})")
        except Exception as e:
            print(f"[Places] search exception: {e}", file=sys.stderr)

    if not found:
        return ""
    return "\n\nFornitori/stakeholder reali (Google Places):\n" + "\n".join(found[:10])


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


def _extract_json(raw):
    raw = raw.replace("```json", "").replace("```", "").strip()
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return None, raw[:300]
    try:
        result = json_repair.loads(m.group())
        if isinstance(result, dict):
            return result, None
        return None, f"Unexpected type {type(result)}"
    except Exception as e:
        return None, f"{e} | raw: {m.group()[:300]}"


_COMPLIANCE_SYSTEM = (
    "Sei il Compliance Auditor del framework QEN (Quantification of Ethical Naturalness).\n"
    "Analizza l'azienda o il sistema AI descritto applicando:\n"
    "- EU AI Act (Allegati I/II/III, livelli rischio)\n"
    "- GDPR (Art.22 decisioni automatizzate, Art.35 DPIA)\n"
    "- CSRD / Green Claims Directive\n"
    "- QEN Score: vs*0.40 + va*0.35 + vt*0.25 (0-100)\n\n"
    "Rispondi SOLO con JSON valido:\n"
    '{"qen_score": 0.0, "vs": 0.0, "va": 0.0, "vt": 0.0, '
    '"eu_ai_act": {"allegato": "", "livello_rischio": "", "motivazione": ""}, '
    '"gdpr": {"risk": "", "dpia_required": false, "articoli": []}, '
    '"gaps": [], "remediation": [], "summary": ""}'
)

_TERRITORIAL_SYSTEM = (
    "Sei il Territorial Mapper del framework QEN.\n"
    "Mappa l'ecosistema territoriale dell'azienda: stakeholder locali, filiera corta,\n"
    "fornitori entro 100km, impatto occupazionale, accordi con PMI locali, DE.CO.\n\n"
    "Rispondi SOLO con JSON valido:\n"
    '{"vt_score": 0.0, "stakeholders": [], "supply_chain": {'
    '"local_pct": 0.0, "avg_distance_km": 0.0, "certifications": []}, '
    '"territorial_impact": "", "recommendations": [], "summary": ""}'
)

_ADVISORY_SYSTEM = (
    "Sei l'Advisory Council del framework QEN — esperto normativo EU.\n"
    "Fornisci consulenza su compliance pathways per:\n"
    "- EU AI Act (percorso conformità per il livello di rischio identificato)\n"
    "- GDPR + CSRD + Green Claims\n"
    "- Bolkestein 2027 (se applicabile al settore)\n\n"
    "Rispondi SOLO con JSON valido:\n"
    '{"priority_actions": [], "compliance_timeline": [], '
    '"regulatory_refs": [], "cost_estimate": "", "summary": ""}'
)


def register_orchestrator(app):
    @app.route("/agents/compliance-auditor", methods=["POST"])
    def compliance_auditor():
        data = request.get_json() or {}
        entity = data.get("entity_name", data.get("name", ""))
        description = data.get("description", data.get("descrizione", ""))
        sector = data.get("sector", data.get("settore", ""))
        if not description:
            return jsonify({"error": "Campo description obbligatorio"}), 400
        prompt = (
            f"Azienda: {entity}\nSettore: {sector}\nDescrizione: {description}"
        )
        try:
            msg = _get_client().messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1500,
                system=_COMPLIANCE_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            result, err = _extract_json(msg.content[0].text)
            if err:
                return jsonify({"error": err}), 500
            result["entity_name"] = entity
            result["timestamp"] = datetime.utcnow().isoformat() + "Z"
            return jsonify({"status": "success", "audit": result}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/agents/territorial-mapper", methods=["POST"])
    def territorial_mapper():
        data = request.get_json() or {}
        entity = data.get("entity_name", data.get("name", ""))
        description = data.get("description", data.get("descrizione", ""))
        location = data.get("location", data.get("comune", "Bologna"))
        if not description:
            return jsonify({"error": "Campo description obbligatorio"}), 400
        places_context = _places_enrich(location)
        prompt = (
            f"Azienda: {entity}\nLocalità: {location}\nDescrizione: {description}"
            + places_context
        )
        try:
            msg = _get_client().messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1200,
                system=_TERRITORIAL_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            result, err = _extract_json(msg.content[0].text)
            if err:
                return jsonify({"error": err}), 500
            result["entity_name"] = entity
            result["timestamp"] = datetime.utcnow().isoformat() + "Z"
            return jsonify({"status": "success", "mapping": result}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/agents/advisory-council", methods=["POST"])
    def advisory_council():
        data = request.get_json() or {}
        entity = data.get("entity_name", data.get("name", ""))
        description = data.get("description", data.get("descrizione", ""))
        sector = data.get("sector", data.get("settore", ""))
        risk_level = data.get("risk_level", "")
        if not description:
            return jsonify({"error": "Campo description obbligatorio"}), 400
        prompt = (
            f"Azienda: {entity}\nSettore: {sector}\n"
            f"Livello rischio identificato: {risk_level}\nDescrizione: {description}"
        )
        try:
            msg = _get_client().messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1200,
                system=_ADVISORY_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            result, err = _extract_json(msg.content[0].text)
            if err:
                return jsonify({"error": err}), 500
            result["entity_name"] = entity
            result["timestamp"] = datetime.utcnow().isoformat() + "Z"
            return jsonify({"status": "success", "advisory": result}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/agents/intelligence-feed", methods=["GET"])
    def intelligence_feed():
        return jsonify({
            "status": "ok",
            "feed": [
                {
                    "id": "EUAIACT-2025-001",
                    "type": "regulatory_update",
                    "title": "EU AI Act — Obligations for high-risk AI systems in force",
                    "date": "2025-08-01",
                    "impact": "HIGH",
                    "sectors": ["all"],
                    "action_required": "Self-assessment + conformity declaration",
                    "deadline": "2026-08-02",
                },
                {
                    "id": "CSRD-2026-001",
                    "type": "regulatory_update",
                    "title": "CSRD — Double materiality assessment deadline",
                    "date": "2026-01-01",
                    "impact": "HIGH",
                    "sectors": ["all_with_employees_gt_250"],
                    "action_required": "ESRS reporting + double materiality",
                    "deadline": "2026-06-30",
                },
                {
                    "id": "BOLKESTEIN-2027-001",
                    "type": "deadline_alert",
                    "title": "Bolkestein Directive 2027 — Service authorizations renewal",
                    "date": "2026-01-01",
                    "impact": "HIGH",
                    "sectors": ["horeca", "balneare", "alberghiero"],
                    "action_required": "QEN pre-assessment + compliance documentation",
                    "deadline": "2027-01-01",
                },
                {
                    "id": "GREENCLAIMS-2026-001",
                    "type": "regulatory_update",
                    "title": "Green Claims Directive — Substantiation requirements",
                    "date": "2026-03-01",
                    "impact": "MEDIUM",
                    "sectors": ["retail", "horeca", "manufacturing"],
                    "action_required": "Third-party verification of environmental claims",
                    "deadline": "2026-12-31",
                },
            ],
            "benchmarks": {
                "horeca_avg_qen": 43.5,
                "alberghiero_avg_qen": 51.2,
                "balneare_avg_qen": 38.7,
                "emilia_romagna_total_mapped": 328,
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }), 200

    @app.route("/agents/mistral-compliance", methods=["POST"])
    def mistral_compliance():
        data = request.get_json() or {}
        entity = data.get("entity_name", data.get("name", ""))
        description = data.get("description", data.get("descrizione", ""))
        sector = data.get("sector", data.get("settore", ""))
        if not description:
            return jsonify({"error": "Campo description obbligatorio"}), 400
        key = os.getenv("MISTRAL_API_KEY", "")
        if not key:
            return jsonify({"error": "MISTRAL_API_KEY non configurata"}), 503
        prompt = f"Azienda: {entity}\nSettore: {sector}\nDescrizione: {description}"
        try:
            resp = _requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": "mistral-large-latest",
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": _COMPLIANCE_SYSTEM},
                        {"role": "user", "content": prompt},
                    ],
                },
                timeout=60,
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]
            result, err = _extract_json(raw)
            if err:
                return jsonify({"error": err}), 500
            result["entity_name"] = entity
            result["provider"] = "mistral-large-latest"
            result["timestamp"] = datetime.utcnow().isoformat() + "Z"
            return jsonify({"status": "success", "audit": result}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/agents/openai-advisor", methods=["POST"])
    def openai_advisor():
        data = request.get_json() or {}
        entity = data.get("entity_name", data.get("name", ""))
        description = data.get("description", data.get("descrizione", ""))
        sector = data.get("sector", data.get("settore", ""))
        risk_level = data.get("risk_level", "")
        if not description:
            return jsonify({"error": "Campo description obbligatorio"}), 400
        key = os.getenv("OPENAI_API_KEY", "")
        if not key:
            return jsonify({"error": "OPENAI_API_KEY non configurata"}), 503
        prompt = (
            f"Azienda: {entity}\nSettore: {sector}\n"
            f"Livello rischio identificato: {risk_level}\nDescrizione: {description}"
        )
        try:
            resp = _requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": _ADVISORY_SYSTEM},
                        {"role": "user", "content": prompt},
                    ],
                },
                timeout=60,
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]
            result, err = _extract_json(raw)
            if err:
                return jsonify({"error": err}), 500
            result["entity_name"] = entity
            result["provider"] = "gpt-4o-mini"
            result["timestamp"] = datetime.utcnow().isoformat() + "Z"
            return jsonify({"status": "success", "advisory": result}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
