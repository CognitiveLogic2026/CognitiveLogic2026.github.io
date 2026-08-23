# Copyright (c) 2026 Roberto Bob Malini - Cognitive Logic
# https://www.cognitivelogic.it
# Licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
import os
import json
import re
from datetime import datetime, UTC

import json_repair
import requests as _requests
from pathlib import Path
from flask import request, jsonify
from sovereign_engine import compliance_audit as sovereign_compliance_audit
from sovereign_engine import territorial_map as sovereign_territorial_map
from sovereign_engine import advisory_assessment as sovereign_advisory_assessment
from sovereign_engine import score_entity as sovereign_score_entity

_FEED_PATH = Path(__file__).parent / "data" / "intelligence_feed.json"


_PLACES_QUERIES = {
    "balneare":    [
        "stabilimento balneare {comune}",
        "lido balneare {comune}",
        "beach club {comune}",
    ],
    "horeca":      [
        "ristorante trattoria {comune}",
        "pizzeria {comune}",
        "osteria {comune}",
    ],
    "alberghiero": [
        "hotel {comune}",
        "albergo bed and breakfast {comune}",
    ],
    "commercio":   [
        "negozio mercato {comune}",
        "bottega artigiana {comune}",
    ],
}


def _places_discover(key: str, settore: str, comune: str, max_results: int = 20) -> list:
    """Discover businesses via Google Places Text Search by settore and comune."""
    import sys
    templates = _PLACES_QUERIES.get(settore, [f"{settore} {comune}"])
    found: dict = {}
    for tpl in templates:
        q = tpl.format(comune=comune)
        try:
            resp = _requests.post(
                "https://places.googleapis.com/v1/places:searchText",
                headers={
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": key,
                    "X-Goog-FieldMask": (
                        "places.displayName,places.formattedAddress,"
                        "places.nationalPhoneNumber,places.websiteUri,"
                        "places.rating,places.userRatingCount,places.primaryType"
                    ),
                },
                json={"textQuery": q, "maxResultCount": min(max_results, 20)},
                timeout=8,
            ).json()
            for p in resp.get("places", []):
                name = p.get("displayName", {}).get("text", "")
                if not name or name in found:
                    continue
                found[name] = {
                    "name":    name,
                    "address": p.get("formattedAddress", ""),
                    "phone":   p.get("nationalPhoneNumber", ""),
                    "website": p.get("websiteUri", ""),
                    "rating":  p.get("rating"),
                    "reviews": p.get("userRatingCount"),
                    "type":    p.get("primaryType", ""),
                    "settore": settore,
                    "comune":  comune,
                }
                if len(found) >= max_results:
                    break
            print(f"[Places] discover q={q!r} → {len(resp.get('places', []))} hits", file=sys.stderr)
        except Exception as e:
            print(f"[Places] discover exception: {e}", file=sys.stderr)
        if len(found) >= max_results:
            break
    return list(found.values())


def _discovery_save_pilot(name: str, score_data: dict):
    """Save a discovered business to pilots.json (minimal inline write)."""
    import sys
    pilots_path = "/app/cognitivelogic/pilots.json"
    try:
        try:
            with open(pilots_path, "r") as f:
                pilots = json.load(f)
        except Exception:
            pilots = {}
        k = name.strip().lower()
        entry = {
            "name": name,
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "data": score_data,
        }
        if k in pilots:
            pilots[k].setdefault("history", []).append(pilots[k].get("data", {}))
        pilots[k] = entry
        with open(pilots_path, "w") as f:
            json.dump(pilots, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Discovery] save_pilot error: {e}", file=sys.stderr)


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


_DISCOVERY_QEN_SYSTEM = (
    "Sei il Discovery Pre-Assessor del framework QEN (Quantification of Ethical Naturalness).\n"
    "Ricevi dati pubblici minimi su un'attività commerciale (nome, tipologia, indirizzo, valutazioni).\n"
    "Stima un QEN pre-assessment per il settore HoReCa / balneare / commercio:\n"
    "- Vs (Semantic Legality): conformità regolatoria presunta per il settore (0-100)\n"
    "- Va (Accountability): trasparenza e responsabilità presunta (0-100)\n"
    "- Vt (Territorial Trust): radicamento territoriale e impatto locale presunto (0-100)\n"
    "Formula: qen_score = Vs*0.40 + Va*0.35 + Vt*0.25\n\n"
    "IMPORTANTE: Questa è una stima basata su dati pubblici limitati, non un audit completo.\n\n"
    "Rispondi SOLO con JSON valido:\n"
    '{"qen_score": 0.0, "vs": 0.0, "va": 0.0, "vt": 0.0, '
    '"confidence": "LOW|MEDIUM", '
    '"risk_flags": [], '
    '"bolkestein_applicable": false, '
    '"summary": "", '
    '"note": "Pre-assessment da dati pubblici — audit completo consigliato"}'
)


_BOLKESTEIN_SYSTEM = (
    "Sei un esperto della Direttiva Servizi EU 2006/123/CE (Bolkestein) e del suo impatto sulle\n"
    "concessioni italiane con scadenza 2027 (balneari, mercati, dehors, posteggi, taxi).\n"
    "Applica il test di scarsità della risorsa, le ragioni imperative di interesse generale (RIGI),\n"
    "la giurisprudenza CGUE (C-458/14, C-20/21) e il QEN Score per la valutazione d'impatto.\n\n"
    "Rispondi SOLO con JSON valido:\n"
    '{"risk_level": "ALTO|MEDIO|BASSO", '
    '"concession_type": "", '
    '"scarcity_test": {"result": "SCARSA|NON_SCARSA|INCERTA", "justification": ""}, '
    '"imperative_reasons": [], '
    '"compliance_actions": [], '
    '"critical_deadlines": [{"date": "", "action": ""}], '
    '"qen_preassessment": {"score": 0.0, "vs": 0.0, "va": 0.0, "vt": 0.0, "note": ""}, '
    '"regulatory_refs": [], '
    '"summary": ""}'
)


def _score_business_list(
    businesses: list,
    settore: str,
    provider: str = "qen-sovereign",
    auto_save: bool = False,
) -> list:
    results = []

    for biz in businesses:
        name = biz.get("name", "")
        if not name:
            continue

        biz_settore = biz.get("settore") or settore
        description = (
            f"Attività: {name}. "
            f"Tipologia: {biz.get('type', biz_settore)}. "
            f"Indirizzo: {biz.get('address', '')}."
        )

        if biz.get("rating"):
            description += (
                f" Valutazione clienti: {biz['rating']}/5 "
                f"({biz.get('reviews', 0)} recensioni)."
            )

        scored = dict(biz)
        scored.update(
            sovereign_score_entity(
                name=name,
                description=description,
                sector=biz_settore,
            )
        )
        scored["status"] = "PRE_ASSESSMENT"

        if auto_save:
            _discovery_save_pilot(name, scored)

        results.append(scored)

    return results

def register_orchestrator(app, limiter=None):
    _lim = limiter.limit if limiter else lambda _: (lambda f: f)
    @app.route("/agents/compliance-auditor", methods=["POST"])
    @_lim("30 per minute")
    def compliance_auditor():
        data = request.get_json() or {}
        entity = data.get("entity_name", data.get("name", ""))
        description = data.get("description", data.get("descrizione", ""))
        sector = data.get("sector", data.get("settore", ""))

        if not description:
            return jsonify({"error": "Campo description obbligatorio"}), 400

        result = sovereign_compliance_audit(
            entity_name=entity,
            description=description,
            sector=sector,
        )
        return jsonify({"status": "success", "audit": result}), 200

    @app.route("/agents/territorial-mapper", methods=["POST"])
    @_lim("30 per minute")
    def territorial_mapper():
        data = request.get_json() or {}
        entity = data.get("entity_name", data.get("name", ""))
        description = data.get("description", data.get("descrizione", ""))
        location = data.get("location", data.get("comune", "Bologna"))

        if not description:
            return jsonify({"error": "Campo description obbligatorio"}), 400

        places_context = _places_enrich(location)
        result = sovereign_territorial_map(
            entity_name=entity,
            description=description,
            location=location,
            places_context=places_context,
        )
        return jsonify({"status": "success", "mapping": result}), 200

    @app.route("/agents/advisory-council", methods=["POST"])
    @_lim("30 per minute")
    def advisory_council():
        data = request.get_json() or {}
        entity = data.get("entity_name", data.get("name", ""))
        description = data.get("description", data.get("descrizione", ""))
        sector = data.get("sector", data.get("settore", ""))
        risk_level = data.get("risk_level", "")

        if not description:
            return jsonify({"error": "Campo description obbligatorio"}), 400

        result = sovereign_advisory_assessment(
            entity_name=entity,
            description=description,
            sector=sector,
            risk_level=risk_level,
        )
        return jsonify({"status": "success", "advisory": result}), 200

    @app.route("/agents/intelligence-feed", methods=["GET"])
    def intelligence_feed():
        try:
            payload = json.loads(_FEED_PATH.read_text(encoding="utf-8"))
        except Exception:
            payload = {"feed": [], "benchmarks": {}}
        payload["status"] = "ok"
        payload["timestamp"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        return jsonify(payload), 200

    # ---------------------------------------------------------------------------
    # Deprecated provider-named compatibility routes backed exclusively by QEN Sovereign


    @app.after_request
    def add_legacy_agent_deprecation_headers(response):
        """Mark provider-named agent routes as sovereign compatibility routes."""
        legacy_routes = {
            "/agents/mistral-compliance": "/agents/compliance-auditor",
            "/agents/mistral-advisor": "/agents/advisory-council",
        }

        successor = legacy_routes.get(request.path)

        if successor:
            response.headers["Deprecation"] = "true"
            response.headers["Link"] = (
                f'<{successor}>; rel="successor-version"'
            )
            response.headers["X-QEN-Compatibility-Route"] = (
                "legacy-provider-agent"
            )

        return response


    @app.route("/agents/mistral-compliance", methods=["POST"])
    @_lim("30 per minute")
    def mistral_compliance():
        """Compatibility endpoint backed exclusively by the Sovereign Engine."""
        data = request.get_json() or {}
        entity = data.get("entity_name", data.get("name", ""))
        description = data.get("description", data.get("descrizione", ""))
        sector = data.get("sector", data.get("settore", ""))

        if not description:
            return jsonify({"error": "Campo description obbligatorio"}), 400

        result = sovereign_compliance_audit(
            entity_name=entity,
            description=description,
            sector=sector,
        )

        return jsonify({
            "status": "success",
            "audit": result,
        }), 200

    @app.route("/agents/mistral-advisor", methods=["POST"])
    @_lim("30 per minute")
    def mistral_advisor():
        """Compatibility endpoint backed exclusively by the Sovereign Engine."""
        data = request.get_json() or {}
        entity = data.get("entity_name", data.get("name", ""))
        description = data.get("description", data.get("descrizione", ""))
        sector = data.get("sector", data.get("settore", ""))
        risk_level = data.get("risk_level", "")

        if not description:
            return jsonify({"error": "Campo description obbligatorio"}), 400

        result = sovereign_advisory_assessment(
            entity_name=entity,
            description=description,
            sector=sector,
            risk_level=risk_level,
        )

        return jsonify({
            "status": "success",
            "advisory": result,
        }), 200

    @app.route("/agents/bolkestein-assessment", methods=["POST"])
    @_lim("30 per minute")
    def bolkestein_assessment():
        data = request.get_json() or {}
        entity = data.get("entity_name", data.get("name", ""))
        description = data.get("description", data.get("descrizione", ""))
        sector = data.get("sector", data.get("settore", ""))
        location = data.get("location", data.get("comune", ""))
        concessione = data.get("concessione_tipo", "")
        scadenza = data.get("scadenza_attuale", "2027-12-31")

        if not description:
            return jsonify({"error": "Campo description obbligatorio"}), 400

        context = (
            f"{description} "
            f"Tipo concessione: {concessione}. "
            f"Località: {location}. "
            f"Scadenza attuale: {scadenza}."
        )

        result = sovereign_compliance_audit(
            entity_name=entity,
            description=context,
            sector=sector,
        )
        result["concession_type"] = concessione
        result["location"] = location
        result["current_deadline"] = scadenza
        result["deadline_2027"] = "2027-01-01"
        result["provider"] = "qen-sovereign"

        return jsonify({
            "status": "success",
            "assessment": result,
        }), 200

    # -----------------------------------------------------------------------
    # Google Places discovery endpoints
    # -----------------------------------------------------------------------

    @app.route("/agents/places-discovery", methods=["POST"])
    def places_discovery():
        data = request.get_json() or {}
        comune      = (data.get("comune") or "Bologna").strip()
        settore     = (data.get("settore") or "horeca").strip().lower()
        max_results = min(int(data.get("max_results", 20)), 50)
        key = os.getenv("GOOGLE_PLACES_API_KEY", "")
        if not key:
            return jsonify({"error": "GOOGLE_PLACES_API_KEY non configurata"}), 503
        businesses = _places_discover(key, settore, comune, max_results)
        return jsonify({
            "status":     "success",
            "comune":     comune,
            "settore":    settore,
            "total":      len(businesses),
            "businesses": businesses,
            "timestamp":  datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }), 200

    @app.route("/agents/score-businesses", methods=["POST"])
    @_lim("20 per minute")
    def score_businesses():
        data      = request.get_json() or {}
        businesses = data.get("businesses", [])[:5]
        provider  = "qen-sovereign"
        auto_save = bool(data.get("auto_save", False))
        settore   = (data.get("settore") or "").strip()
        results   = _score_business_list(businesses, settore, provider, auto_save)
        return jsonify({
            "status":    "success",
            "total":     len(results),
            "scored":    results,
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }), 200

    @app.route("/agents/places-batch-qen", methods=["POST"])
    @_lim("20 per minute")
    def places_batch_qen():
        data        = request.get_json() or {}
        comune      = (data.get("comune") or "Bologna").strip()
        settore     = (data.get("settore") or "horeca").strip().lower()
        max_results = min(int(data.get("max_results", 10)), 20)
        provider    = "qen-sovereign"
        auto_save   = bool(data.get("auto_save", False))

        key_places = os.getenv("GOOGLE_PLACES_API_KEY", "")
        if not key_places:
            return jsonify({"error": "GOOGLE_PLACES_API_KEY non configurata"}), 503

        businesses = _places_discover(key_places, settore, comune, max_results)
        if not businesses:
            return jsonify({
                "status": "success", "scored": [], "total": 0,
                "comune": comune, "settore": settore,
            }), 200

        results = _score_business_list(businesses, settore, provider, auto_save)
        return jsonify({
            "status":     "success",
            "comune":     comune,
            "settore":    settore,
            "total":      len(results),
            "auto_saved": auto_save,
            "scored":     results,
            "timestamp":  datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }), 200
