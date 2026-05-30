# Copyright (c) 2026 Roberto Bob Malini - Cognitive Logic
# https://www.cognitivelogic.it
# Licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
import os
import json
import re
from datetime import datetime

import anthropic
import json_repair
import requests as _requests
from flask import request, jsonify

_client = None


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
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
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

    # ---------------------------------------------------------------------------
    # Mistral endpoints (primary LLM — Mistral Large via REST, no SDK)
    # MISTRAL_API_KEY injected from GitHub Secrets at deploy time
    # Falls back to Claude Sonnet if Mistral is unavailable
    # ---------------------------------------------------------------------------

    def _mistral_chat(key: str, system: str, prompt: str) -> str:
        """Call Mistral Large and return the raw content string."""
        resp = _requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "mistral-large-latest",
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=45,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

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
        provider = "mistral-large-latest"
        try:
            raw = _mistral_chat(key, _COMPLIANCE_SYSTEM, prompt)
        except Exception as mistral_err:
            # Fallback: Claude Sonnet if Mistral fails
            try:
                msg = _get_client().messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=1500,
                    system=_COMPLIANCE_SYSTEM,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw = msg.content[0].text
                provider = "claude-sonnet-4-6-fallback"
            except Exception as claude_err:
                return jsonify({"error": f"Mistral: {mistral_err} | Claude fallback: {claude_err}"}), 500
        result, err = _extract_json(raw)
        if err:
            return jsonify({"error": err}), 500
        result["entity_name"] = entity
        result["provider"] = provider
        result["timestamp"] = datetime.utcnow().isoformat() + "Z"
        return jsonify({"status": "success", "audit": result}), 200

    @app.route("/agents/mistral-advisor", methods=["POST"])
    def mistral_advisor():
        data = request.get_json() or {}
        entity = data.get("entity_name", data.get("name", ""))
        description = data.get("description", data.get("descrizione", ""))
        sector = data.get("sector", data.get("settore", ""))
        risk_level = data.get("risk_level", "")
        if not description:
            return jsonify({"error": "Campo description obbligatorio"}), 400
        key = os.getenv("MISTRAL_API_KEY", "")
        if not key:
            return jsonify({"error": "MISTRAL_API_KEY non configurata"}), 503
        prompt = (
            f"Azienda: {entity}\nSettore: {sector}\n"
            f"Livello rischio identificato: {risk_level}\nDescrizione: {description}"
        )
        provider = "mistral-large-latest"
        try:
            raw = _mistral_chat(key, _ADVISORY_SYSTEM, prompt)
        except Exception as mistral_err:
            # Fallback: Claude Sonnet if Mistral fails
            try:
                msg = _get_client().messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=1200,
                    system=_ADVISORY_SYSTEM,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw = msg.content[0].text
                provider = "claude-sonnet-4-6-fallback"
            except Exception as claude_err:
                return jsonify({"error": f"Mistral: {mistral_err} | Claude fallback: {claude_err}"}), 500
        result, err = _extract_json(raw)
        if err:
            return jsonify({"error": err}), 500
        result["entity_name"] = entity
        result["provider"] = provider
        result["timestamp"] = datetime.utcnow().isoformat() + "Z"
        return jsonify({"status": "success", "advisory": result}), 200

    # ---------------------------------------------------------------------------
    # OpenAI endpoint — DISABLED (payment pending, OPENAI_API_KEY non disponibile)
    # ---------------------------------------------------------------------------
    # @app.route("/agents/openai-advisor", methods=["POST"])
    # def openai_advisor():
    #     ...  # gpt-4o-mini via https://api.openai.com/v1/chat/completions
    # ---------------------------------------------------------------------------

    @app.route("/agents/openai-advisor", methods=["POST"])
    def openai_advisor():
        return jsonify({
            "error": "OpenAI endpoint disabilitato (pagamento in sospeso). Usa /agents/mistral-advisor.",
            "alternative": "/agents/mistral-advisor",
        }), 503

    @app.route("/agents/bolkestein-assessment", methods=["POST"])
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
        prompt = (
            f"Azienda: {entity}\n"
            f"Settore: {sector}\n"
            f"Tipo concessione: {concessione}\n"
            f"Localita: {location}\n"
            f"Scadenza concessione attuale: {scadenza}\n"
            f"Descrizione attivita: {description}\n\n"
            "Esegui il Bolkestein 2027 pre-assessment completo."
        )
        key = os.getenv("MISTRAL_API_KEY", "")
        provider = "mistral-large-latest"
        try:
            if key:
                raw = _mistral_chat(key, _BOLKESTEIN_SYSTEM, prompt)
            else:
                raise RuntimeError("MISTRAL_API_KEY non configurata")
        except Exception as mistral_err:
            try:
                msg = _get_client().messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=1500,
                    system=_BOLKESTEIN_SYSTEM,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw = msg.content[0].text
                provider = "claude-sonnet-4-6-fallback"
            except Exception as claude_err:
                return jsonify({"error": f"Mistral: {mistral_err} | Claude fallback: {claude_err}"}), 500
        result, err = _extract_json(raw)
        if err:
            return jsonify({"error": err}), 500
        result["entity_name"] = entity
        result["provider"] = provider
        result["deadline_2027"] = "2027-01-01"
        result["timestamp"] = datetime.utcnow().isoformat() + "Z"
        return jsonify({"status": "success", "assessment": result}), 200

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
            "timestamp":  datetime.utcnow().isoformat() + "Z",
        }), 200

    @app.route("/agents/score-businesses", methods=["POST"])
    def score_businesses():
        """Score a pre-discovered list of businesses (max 5 per call, no re-discovery)."""
        import time
        data       = request.get_json() or {}
        businesses = data.get("businesses", [])[:5]
        provider   = (data.get("provider") or "mistral").lower()
        auto_save  = bool(data.get("auto_save", False))
        settore    = (data.get("settore") or "").strip()

        results = []
        for biz in businesses:
            name = biz.get("name", "")
            if not name:
                continue
            desc = (
                f"Attività: {name}. "
                f"Tipologia: {biz.get('type', settore)}. "
                f"Indirizzo: {biz.get('address', '')}."
            )
            if biz.get("rating"):
                desc += f" Valutazione clienti: {biz['rating']}/5 ({biz.get('reviews', 0)} recensioni)."
            prompt = (
                f"Azienda: {name}\nSettore: {biz.get('settore', settore)}\n"
                f"Comune: {biz.get('comune', '')}\nDescrizione: {desc}"
            )
            scored = dict(biz)
            raw = None
            try:
                if provider == "mistral":
                    mk = os.getenv("MISTRAL_API_KEY", "")
                    if mk:
                        raw = _mistral_chat(mk, _DISCOVERY_QEN_SYSTEM, prompt)
                    else:
                        raise RuntimeError("no mistral key")
                else:
                    raise RuntimeError("use claude")
            except Exception:
                try:
                    msg = _get_client().messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=600,
                        system=_DISCOVERY_QEN_SYSTEM,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    raw = msg.content[0].text
                except Exception as e:
                    scored["error"] = str(e)
                    results.append(scored)
                    continue
            audit, err = _extract_json(raw)
            if audit:
                scored.update({
                    "qen_score":             audit.get("qen_score"),
                    "vs":                    audit.get("vs"),
                    "va":                    audit.get("va"),
                    "vt":                    audit.get("vt"),
                    "confidence":            audit.get("confidence", "LOW"),
                    "risk_flags":            audit.get("risk_flags", []),
                    "bolkestein_applicable": audit.get("bolkestein_applicable", False),
                    "summary":               audit.get("summary", ""),
                    "note":                  audit.get("note", ""),
                    "status":                "PRE_ASSESSMENT",
                })
                if auto_save and audit.get("qen_score") is not None:
                    _discovery_save_pilot(name, scored)
            else:
                scored["error"] = err
            results.append(scored)
            # small delay to avoid Mistral rate-limit on consecutive calls
            if len(results) < len(businesses):
                time.sleep(0.5)

        return jsonify({
            "status":  "success",
            "total":   len(results),
            "scored":  results,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }), 200

    @app.route("/agents/places-batch-qen", methods=["POST"])
    def places_batch_qen():
        import sys
        data        = request.get_json() or {}
        comune      = (data.get("comune") or "Bologna").strip()
        settore     = (data.get("settore") or "horeca").strip().lower()
        max_results = min(int(data.get("max_results", 10)), 20)
        provider    = (data.get("provider") or "mistral").lower()
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

        results = []
        for biz in businesses:
            desc = (
                f"Attività: {biz['name']}. "
                f"Tipologia: {biz.get('type', settore)}. "
                f"Indirizzo: {biz['address']}."
            )
            if biz.get("rating"):
                desc += f" Valutazione clienti: {biz['rating']}/5 ({biz.get('reviews', 0)} recensioni)."
            prompt = (
                f"Azienda: {biz['name']}\nSettore: {settore}\n"
                f"Comune: {comune}\nDescrizione: {desc}"
            )
            scored = dict(biz)
            raw = None
            try:
                if provider == "mistral":
                    mk = os.getenv("MISTRAL_API_KEY", "")
                    if mk:
                        raw = _mistral_chat(mk, _DISCOVERY_QEN_SYSTEM, prompt)
                    else:
                        raise RuntimeError("no mistral key")
                else:
                    raise RuntimeError("use claude")
            except Exception:
                try:
                    msg = _get_client().messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=600,
                        system=_DISCOVERY_QEN_SYSTEM,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    raw = msg.content[0].text
                except Exception as e:
                    scored["error"] = str(e)
                    results.append(scored)
                    continue
            audit, err = _extract_json(raw)
            if audit:
                scored.update({
                    "qen_score":            audit.get("qen_score"),
                    "vs":                   audit.get("vs"),
                    "va":                   audit.get("va"),
                    "vt":                   audit.get("vt"),
                    "confidence":           audit.get("confidence", "LOW"),
                    "risk_flags":           audit.get("risk_flags", []),
                    "bolkestein_applicable": audit.get("bolkestein_applicable", False),
                    "summary":              audit.get("summary", ""),
                    "note":                 audit.get("note", ""),
                    "status":               "PRE_ASSESSMENT",
                })
                if auto_save and audit.get("qen_score") is not None:
                    _discovery_save_pilot(biz["name"], scored)
            else:
                scored["error"] = err
            results.append(scored)

        return jsonify({
            "status":     "success",
            "comune":     comune,
            "settore":    settore,
            "total":      len(results),
            "auto_saved": auto_save,
            "scored":     results,
            "timestamp":  datetime.utcnow().isoformat() + "Z",
        }), 200
