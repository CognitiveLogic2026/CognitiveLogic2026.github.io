# Copyright (c) 2026 Roberto Bob Malini - Cognitive Logic
# https://www.cognitivelogic.it
# Licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
import fcntl
import hashlib
import os
import hmac
import json
import re
from pathlib import Path
import requests as _requests
try:
    import anthropic
except ImportError:
    anthropic = None
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sovereign_engine import classify_risk as sovereign_classify_risk
from sovereign_engine import score_entity as sovereign_score_entity

app = Flask(__name__)

limiter = Limiter(app=app, key_func=get_remote_address, default_limits=[], storage_uri=os.getenv("REDIS_URL", "memory://"))

_CORS_ORIGINS = frozenset({
    "https://cognitivelogic.it",
    "https://www.cognitivelogic.it",
    "https://api.cognitivelogic.it",
})

def _key_ok(provided: str | None, env_var: str = "COGNITIVE_API_KEY") -> bool:
    """Timing-safe API key comparison."""
    expected = os.getenv(env_var, "")
    return bool(expected) and hmac.compare_digest(provided or "", expected)

def _qen(vs: float, va: float, vt: float) -> float:
    return round(vs * 0.40 + va * 0.35 + vt * 0.25, 2)

def _verdict_for_qen(score: float) -> str:
    """Map a QEN total to an EVIDE verdict using the published thresholds
    (<60 critico, 60-70 medio, 70-85 buono, >85 eccellente)."""
    if score < 60:
        return "NON_COMPLIANT"
    if score < 70:
        return "REVIEW_REQUIRED"
    return "COMPLIANT"


_TRUSTED_HOSTS = frozenset({
    "cognitivelogic.it",
    "www.cognitivelogic.it",
    "api.cognitivelogic.it",
})

def _require_trusted_origin():
    """Return a 403 response if the call doesn't come from a trusted origin/referer
    AND doesn't carry a valid X-API-Key. Protects cost-bearing public endpoints."""
    api_key = request.headers.get("X-API-Key", "")
    if _key_ok(api_key):
        return None  # authenticated call — always allowed

    origin   = request.headers.get("Origin", "")
    referer  = request.headers.get("Referer", "")

    def _trusted(url: str) -> bool:
        from urllib.parse import urlparse
        host = urlparse(url).hostname or ""
        return host in _TRUSTED_HOSTS

    if origin and _trusted(origin):
        return None
    if referer and _trusted(referer):
        return None

    return jsonify({"error": "Forbidden", "detail": "Untrusted origin"}), 403


@app.before_request
def handle_preflight():
    if request.method == 'OPTIONS':
        resp = app.make_response('')
        resp.status_code = 204
        return resp

@app.after_request
def add_cors(response):
    origin = request.headers.get('Origin', '')
    if origin in _CORS_ORIGINS:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-API-Key'
    return response

GRAPH_PATH   = "/app/cognitivelogic/graph.json"
PILOTS_PATH  = "/app/cognitivelogic/pilots.json"
ANTHROPIC_CLIENT = None

def get_anthropic_client():
    global ANTHROPIC_CLIENT
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic is None or not api_key:
        return None
    if ANTHROPIC_CLIENT is None:
        ANTHROPIC_CLIENT = anthropic.Anthropic(api_key=api_key)
    return ANTHROPIC_CLIENT

def load_pilots():
    if not os.path.exists(PILOTS_PATH):
        return {}
    with open(PILOTS_PATH, "r") as f:
        return json.load(f)

_PILOTS_LOCK_PATH = PILOTS_PATH + ".lock"

def save_pilot(name, score_data):
    Path(_PILOTS_LOCK_PATH).touch(exist_ok=True)
    with open(_PILOTS_LOCK_PATH, "r") as _lf:
        fcntl.flock(_lf, fcntl.LOCK_EX)
        try:
            pilots = load_pilots()
            key = name.strip().lower()
            entry = {
                "name":      name,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "data":      score_data
            }
            if key in pilots:
                pilots[key]["history"] = pilots[key].get("history", [])
                pilots[key]["history"].append(pilots[key].get("data", {}))
                pilots[key].update(entry)
            else:
                pilots[key] = entry
            with open(PILOTS_PATH, "w") as f:
                json.dump(pilots, f, indent=2, ensure_ascii=False)
        finally:
            fcntl.flock(_lf, fcntl.LOCK_UN)

def load_pilot(name):
    pilots = load_pilots()
    key = name.strip().lower()
    return pilots.get(key)

def check_duplicate(name):
    return load_pilot(name)

@app.route("/")
def root_health():
    return jsonify({"status": "OPERATIONAL", "version": "1.0.0"})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "CognitiveLogic QEN API", "version": "3.2"}), 200

@app.route("/pilots", methods=["GET"])
def list_pilots():
    if not _key_ok(request.headers.get("X-API-Key")):
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    pilots = load_pilots()
    summary = []
    for key, v in pilots.items():
        d = v.get("data", {})
        qen = d.get("qen_score") or d.get("risk_score")
        if qen is None and isinstance(d.get("qen"), dict):
            qen = d["qen"].get("qen_score")
        summary.append({
            "name":      v.get("name"),
            "timestamp": v.get("timestamp"),
            "qen_score": qen,
            "analyses":  1 + len(v.get("history", []))
        })
    summary.sort(key=lambda x: x["timestamp"] or "", reverse=True)
    return jsonify({"total": len(summary), "pilots": summary}), 200

@app.route("/analyze", methods=["POST"])
def analyze():
    if not _key_ok(request.headers.get("X-API-Key")):
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    data = request.json
    name   = data.get("system_name", "Unknown")
    social = data.get("social_impact", 0)
    env    = data.get("environmental_impact", 0)
    terr   = data.get("territorial_impact", 0)
    qen_score = _qen(social, env, terr)
    evide_entry = _evide_append(
        entry_type="QEN_SCORE", agent="cognitivelogic-api", operator_id=name,
        input_obj={"social_impact": social, "environmental_impact": env, "territorial_impact": terr},
        output_obj={"qen_score": qen_score},
        qen_score=qen_score, verdict=_verdict_for_qen(qen_score),
    )
    new_node = {"id": name, "type": "System", "qen": qen_score, "evide_id": evide_entry["id"],
                "status": "Analyzed", "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}
    try:
        with open(GRAPH_PATH, "r") as f:
            g = json.load(f)
        g["nodes"][name] = new_node
        with open(GRAPH_PATH, "w") as f:
            json.dump(g, f, indent=2)
    except Exception:
        pass
    return jsonify({"status": "success", "qen_score": qen_score, "node": new_node}), 200

@app.route("/audit/horeca", methods=["POST"])
def audit_horeca():
    if not _key_ok(request.headers.get("X-API-Key")):
        return jsonify({"error": "Unauthorized"}), 403
    data = request.json or {}
    nome     = (data.get("azienda_nome") or "Azienda HoReCa").strip()
    coperti  = data.get("coperti", 0)
    qen      = data.get("qen_score_finale", 0)
    mods     = data.get("moduli_dettagliati", {})
    status   = data.get("status_conformita", "")
    audit_id = data.get("qen_audit_id") or "qen-" + datetime.utcnow().strftime("%Y%m%d%H%M%S")

    def ms(key):
        return mods.get(key, {}).get("score", 0) or 0

    vs = round((ms("sociale") + ms("governance")) / 2, 1)
    va = round((ms("imballaggi") + ms("risorse") + ms("qualita") + ms("rifiuti")) / 4, 1)
    vt = round((ms("logistica") + ms("territorio")) / 2, 1)

    score_data = {
        "qen_score": qen, "vs": vs, "va": va, "vt": vt,
        "status": status, "settore": "HoReCa",
        "coperti": coperti, "moduli": mods, "audit_id": audit_id,
    }
    save_pilot(nome, score_data)

    evide_entry = _evide_append(
        entry_type="COMPLIANCE_AUDIT", agent="cognitivelogic-api", operator_id=nome,
        input_obj={"coperti": coperti, "moduli_dettagliati": mods},
        output_obj=score_data,
        qen_score=qen, verdict=_verdict_for_qen(qen),
    )
    new_node = {
        "id": nome, "type": "EntitaPilota", "label": nome,
        "settore": "HoReCa",
        "qen_score": {"vs": vs, "va": va, "vt": vt, "totale": qen},
        "evide_id": evide_entry["id"],
        "stato": "AUDIT_COMPLETATO",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    try:
        with open(GRAPH_PATH, "r") as f:
            g = json.load(f)
        g["nodes"][nome] = new_node
        if "meta" in g:
            g["meta"]["nodi"] = len(g["nodes"])
        with open(GRAPH_PATH, "w") as f:
            json.dump(g, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    return jsonify({"status": "saved", "audit_id": audit_id, "node": new_node}), 200

@app.route("/audit/balneare", methods=["POST"])
def audit_balneare():
    if not _key_ok(request.headers.get("X-API-Key")):
        return jsonify({"error": "Unauthorized"}), 403
    data     = request.json or {}
    nome     = (data.get("azienda_nome") or "Operatore Balneare").strip()
    tipo     = data.get("tipo", "balneare")
    qen      = data.get("qen_score_finale", 0)
    scores   = data.get("scores", {})
    audit_id = data.get("qen_audit_id") or "qen-bal-" + datetime.utcnow().strftime("%Y%m%d%H%M%S")

    def sc(key):
        return scores.get(key, 0) or 0

    # M1 Concessione/Bolkestein + M4 Filiera + M6 Digitale → Territoriale
    vt = round((sc("m1") + sc("m4") + sc("m6")) / 3, 1)
    # M2 Sostenibilità → Ambientale
    va = round(sc("m2"), 1)
    # M5 Lavoro + M3 Servizi/Accessibilità → Sociale
    vs = round((sc("m5") + sc("m3")) / 2, 1)

    score_data = {
        "qen_score": qen, "vs": vs, "va": va, "vt": vt,
        "settore": "Balneare", "tipo": tipo,
        "scores": scores, "audit_id": audit_id,
    }
    save_pilot(nome, score_data)

    evide_entry = _evide_append(
        entry_type="COMPLIANCE_AUDIT", agent="cognitivelogic-api", operator_id=nome,
        input_obj={"tipo": tipo, "scores": scores},
        output_obj=score_data,
        qen_score=qen, verdict=_verdict_for_qen(qen),
    )
    new_node = {
        "id": nome, "type": "EntitaPilota", "label": nome,
        "settore": "Balneare", "tipo": tipo,
        "qen_score": {"vs": vs, "va": va, "vt": vt, "totale": qen},
        "evide_id": evide_entry["id"],
        "stato": "AUDIT_COMPLETATO",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    try:
        with open(GRAPH_PATH, "r") as f:
            g = json.load(f)
        g["nodes"][nome] = new_node
        if "meta" in g:
            g["meta"]["nodi"] = len(g["nodes"])
        with open(GRAPH_PATH, "w") as f:
            json.dump(g, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    return jsonify({"status": "saved", "audit_id": audit_id, "node": new_node}), 200

@app.route("/admin/add-client", methods=["POST"])
def admin_add_client():
    if not _key_ok(request.headers.get("X-API-Key")):
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    data    = request.json or {}
    nome    = (data.get("nome") or "Cliente").strip()
    settore = data.get("settore", "Generico")
    vs      = float(data.get("vs", 0))
    va      = float(data.get("va", 0))
    vt      = float(data.get("vt", 0))
    note    = data.get("note", "")
    qen     = _qen(vs, va, vt)

    score_data = {
        "qen_score": qen, "vs": vs, "va": va, "vt": vt,
        "settore": settore, "note": note,
    }
    save_pilot(nome, score_data)

    evide_entry = _evide_append(
        entry_type="QEN_SCORE", agent="cognitivelogic-admin", operator_id=nome,
        input_obj={"vs": vs, "va": va, "vt": vt, "settore": settore, "note": note},
        output_obj=score_data,
        qen_score=qen, verdict=_verdict_for_qen(qen),
    )
    new_node = {
        "id": nome, "type": "EntitaPilota", "label": nome,
        "settore": settore, "note": note,
        "qen_score": {"vs": vs, "va": va, "vt": vt, "totale": qen},
        "evide_id": evide_entry["id"],
        "stato": "INSERITO_MANUALE",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    try:
        with open(GRAPH_PATH, "r") as f:
            g = json.load(f)
        g["nodes"][nome] = new_node
        if "meta" in g:
            g["meta"]["nodi"] = len(g["nodes"])
        with open(GRAPH_PATH, "w") as f:
            json.dump(g, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    return jsonify({"status": "saved", "qen_score": qen, "node": new_node}), 200

RISK_SYSTEM_PROMPT = (
    "Sei un esperto di EU AI Act e GDPR."
    " Analizza il sistema descritto sotto entrambi i profili.\n\n"
    "Rispondi SOLO con un oggetto JSON valido, nessun testo aggiuntivo.\n\n"
    "Schema: allegato I/II/III/Nessuno, livello_rischio Vietato/Alto/Sorveglianza/Minimo,"
    " motivazione, gdpr_risk CRITICO/ALTO/MEDIO/BASSO, gdpr_motivazione,"
    " articoli_rilevanti list, azioni_richieste list, qen_impact,"
    " vs float, va float, vt float.\n\n"
    "Allegato I=vietati art.5, II=alto rischio, III=biometria/migrazione.\n"
    "GDPR: art.6 base giuridica, art.22 decisioni automatizzate, art.35 DPIA.\n"
    "vs/va/vt: 0-100 impatto Sociale/Ambientale/Territoriale."
)

@app.route("/classify-risk", methods=["POST"])
@limiter.limit("30 per minute")
def classify_risk():
    if not _key_ok(request.headers.get("X-API-Key")):
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    data = request.json
    if not data or "descrizione" not in data:
        return jsonify({"status": "error", "message": "Campo descrizione obbligatorio"}), 400
    descrizione = data.get("descrizione", "")
    contesto    = data.get("contesto", "")
    settore     = data.get("settore", "")
    try:
        sovereign = sovereign_classify_risk(
            description=descrizione,
            context=contesto,
            sector=settore,
        )

        level_map = {
            "PROHIBITED": "Vietato",
            "HIGH": "Alto",
            "MEDIUM": "Sorveglianza",
            "LOW": "Minimo",
        }
        gdpr_map = {
            "CRITICAL": "CRITICO",
            "HIGH": "ALTO",
            "MEDIUM": "MEDIO",
            "LOW": "BASSO",
        }

        classification = {
            "allegato": sovereign["eu_classification"].split(" - ", 1)[-1],
            "livello_rischio": level_map.get(
                sovereign["risk_level"], "Minimo"
            ),
            "motivazione": sovereign["summary"],
            "gdpr_risk": gdpr_map.get(
                sovereign["gdpr_risk"], "BASSO"
            ),
            "gdpr_motivazione": (
                "Valutazione GDPR deterministica basata su dati personali, "
                "profilazione e decisioni automatizzate."
            ),
            "articoli_rilevanti": sovereign["gaps"],
            "azioni_richieste": sovereign["recommendations"],
            "qen_impact": sovereign["decision"],
            "vs": sovereign["vs"],
            "va": sovereign["va"],
            "vt": sovereign["vt"],
        }

        return jsonify({
            "status": "success",
            "sistema": descrizione[:80],
            "classificazione": classification,
        }), 200
    except Exception:
        return jsonify({
            "status": "error",
            "message": "Errore interno del server",
        }), 500

@app.route("/copilot-analyze", methods=["POST"])
@limiter.limit("10 per minute;100 per day")
def copilot_analyze():
    blocked = _require_trusted_origin()
    if blocked:
        return blocked

    data = request.get_json(silent=True)
    if not data or "description" not in data:
        return jsonify({"error": "Campo description obbligatorio"}), 400

    descrizione = str(data.get("description", "")).strip()
    if not descrizione:
        return jsonify({"error": "Campo description obbligatorio"}), 400

    entity_name = data.get("entity_name", descrizione[:60])
    force_reanalyze = data.get("force", False)

    existing = check_duplicate(entity_name)
    if existing and not force_reanalyze:
        return jsonify({
            "duplicate": True,
            "message": "Analisi gia presente per " + entity_name + ". Usa force=true per rieseguire.",
            "timestamp": existing.get("timestamp"),
            "cached_data": existing.get("data"),
            "analyses": 1 + len(existing.get("history", [])),
        }), 200

    try:
        sovereign = sovereign_classify_risk(descrizione)

        public_level = (
            "HIGH"
            if sovereign["risk_level"] in {"PROHIBITED", "HIGH"}
            else sovereign["risk_level"]
        )

        output = {
            "risk_level": public_level,
            "risk_score": sovereign["risk_score"],
            "qen_score": sovereign["qen_score"],
            "vs": sovereign["vs"],
            "va": sovereign["va"],
            "vt": sovereign["vt"],
            "summary": sovereign["summary"],
            "why": (
                "Valutazione GDPR deterministica: "
                + sovereign["gdpr_risk"]
            ),
            "gdpr_risk": sovereign["gdpr_risk"],
            "impact": (
                "Impatto QEN calcolato mediante dati intelligibili, "
                "regole deterministiche ed evidenze verificabili."
            ),
            "eu_classification": sovereign["eu_classification"],
            "gaps": sovereign["gaps"],
            "recommendations": sovereign["recommendations"],
            "decision": sovereign["decision"],
        }

        save_pilot(entity_name, output)
        return jsonify(output), 200

    except Exception:
        app.logger.exception("Sovereign Copilot analysis failed")
        return jsonify({"error": "Errore interno del server"}), 500


@app.route("/gemini/qen-score", methods=["POST"])
@limiter.limit("10 per minute;100 per day")
def gemini_qen_score():
    """Legacy-compatible QEN scoring route backed by the sovereign engine."""
    blocked = _require_trusted_origin()
    if blocked:
        return blocked

    data = request.get_json(silent=True) or {}
    name = data.get("business_name", "")
    sector = data.get("sector", "")
    description = data.get("description", "")
    force_reanalyze = bool(data.get("force", False))

    existing = check_duplicate(name)
    if existing and not force_reanalyze:
        return jsonify({
            "duplicate": True,
            "message": (
                "QEN Score gia presente per "
                + name
                + ". Usa force=true per rieseguire."
            ),
            "timestamp": existing.get("timestamp"),
            "cached_data": existing.get("data"),
            "analyses": 1 + len(existing.get("history", [])),
        }), 200

    try:
        sovereign = sovereign_score_entity(
            name=name,
            description=description,
            sector=sector,
        )

        score = sovereign["qen_score"]
        qen = {
            "qen_score": score,
            "badge": "QEN VERIFIED" if score >= 60 else "QEN UNVERIFIED",
            "vs": sovereign["vs"],
            "va": sovereign["va"],
            "vt": sovereign["vt"],
            "sintesi": sovereign["summary"],
            "provider": "qen-sovereign",
            "engine": sovereign.get("engine", "QEN Sovereign Intelligence Engine"),
            "architecture": "ADR-CLE-004",
            "timestamp": sovereign["timestamp"],
        }

        save_pilot(name, qen)
        return jsonify({"status": "success", "qen": qen}), 200

    except Exception:
        app.logger.exception("Sovereign QEN scoring failed")
        return jsonify({
            "status": "error",
            "error": "Errore interno del server",
        }), 500


@app.route("/gemini/compliance-audit", methods=["POST"])
@limiter.limit("10 per minute;100 per day")
def gemini_compliance_audit():
    """Legacy-compatible compliance audit backed by sovereign intelligence."""
    blocked = _require_trusted_origin()
    if blocked:
        return blocked

    data = request.get_json(silent=True) or {}
    name = data.get("system_name", "Unnamed System")
    system_type = data.get("system_type", "")
    domain = data.get("domain", "")
    description = data.get("description", "")
    controls = data.get("controls", "(no controls documented)")

    if not description:
        return jsonify({"error": "Campo description obbligatorio"}), 400

    try:
        context = (
            f"System type: {system_type}. "
            f"Domain: {domain}. "
            f"Current controls: {controls}."
        )

        sovereign = sovereign_classify_risk(
            description=description,
            context=context,
            sector=domain,
        )

        level_map = {
            "PROHIBITED": "Prohibited",
            "HIGH": "High-Risk",
            "MEDIUM": "Limited-Risk",
            "LOW": "Minimal-Risk",
        }
        severity_map = {
            "PROHIBITED": "Critical",
            "HIGH": "High",
            "MEDIUM": "Medium",
            "LOW": "Low",
        }
        recommendation_map = {
            "PROHIBITED": "Prohibit",
            "HIGH": "Remediation Required",
            "MEDIUM": "Conditional Approval",
            "LOW": "Approve",
        }

        gap_labels = {
            "risk_management": "Risk management system",
            "human_oversight": "Human oversight",
            "technical_documentation": "Technical documentation",
            "transparency_notice": "Transparency notice",
            "gdpr_legal_basis": "GDPR legal basis",
            "gdpr_article_22_review": "Automated decision safeguards",
        }

        findings = []
        for index, gap in enumerate(sovereign["gaps"]):
            remediation = (
                sovereign["recommendations"][index]
                if index < len(sovereign["recommendations"])
                else "Documentare e applicare il controllo richiesto."
            )
            findings.append({
                "category": gap_labels.get(gap, gap.replace("_", " ").title()),
                "severity": severity_map[sovereign["risk_level"]],
                "issue": f"Controllo mancante o non sufficientemente documentato: {gap}.",
                "evidence": (
                    "Gap identificato dal QEN Sovereign Intelligence Engine "
                    "mediante regole deterministiche ed evidenze intelligibili."
                ),
                "remediation": remediation,
            })

        mandatory_controls = [
            gap_labels.get(gap, gap.replace("_", " ").title())
            for gap in sovereign["gaps"]
        ]

        escalation_flag = (
            sovereign["risk_level"] == "PROHIBITED"
            or min(sovereign["vs"], sovereign["va"], sovereign["vt"]) < 30
        )

        assessment_date = datetime.now(timezone.utc).date()
        review_date = assessment_date + timedelta(days=90)

        audit = {
            "system_name": name,
            "risk_classification": level_map[sovereign["risk_level"]],
            "domain": domain,
            "assessment_date": assessment_date.isoformat(),
            "scores": {
                "Vs": sovereign["vs"],
                "Va": sovereign["va"],
                "Vt": sovereign["vt"],
                "QEN_SCORE": sovereign["qen_score"],
            },
            "findings": findings,
            "mandatory_controls": mandatory_controls,
            "escalation_flag": escalation_flag,
            "escalation_reason": (
                "Sistema proibito o vettore QEN inferiore alla soglia minima."
                if escalation_flag
                else None
            ),
            "recommendation": recommendation_map[sovereign["risk_level"]],
            "next_steps": sovereign["recommendations"],
            "governance_owner": "AI Governance Owner",
            "review_date": review_date.isoformat(),
            "provider": "qen-sovereign",
            "engine": sovereign["engine"],
            "architecture": sovereign["architecture"],
            "decision_id": sovereign["decision_id"],
            "knowledge_evidence": sovereign["knowledge_evidence"],
        }

        return jsonify({"status": "success", "audit": audit}), 200

    except Exception:
        app.logger.exception("Sovereign compliance audit failed")
        return jsonify({
            "status": "error",
            "error": "Errore interno del server",
        }), 500


_QEN_DRIFT_THRESHOLD = 0.5

@app.route("/admin/reconcile-batch", methods=["POST"])
def reconcile_batch():
    if not _key_ok(request.headers.get("X-API-Key")):
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    pilots = load_pilots()
    report = []
    corrected = 0

    for key, pilot in pilots.items():
        data = pilot.get("data", {})
        vs = data.get("vs")
        va = data.get("va")
        vt = data.get("vt")
        stored_qen = data.get("qen_score") or data.get("risk_score")

        if vs is None or va is None or vt is None or stored_qen is None:
            report.append({"name": pilot.get("name", key), "status": "skipped",
                           "reason": "vs/va/vt/qen_score mancanti"})
            continue

        expected_qen = _qen(float(vs), float(va), float(vt))
        drift = abs(float(stored_qen) - expected_qen)

        if drift > _QEN_DRIFT_THRESHOLD:
            data["qen_score"] = expected_qen
            pilot["data"] = data
            corrected += 1
            report.append({
                "name": pilot.get("name", key), "status": "corrected",
                "old_qen": stored_qen, "new_qen": expected_qen,
                "delta": round(expected_qen - float(stored_qen), 2),
                "reason": f"formula drift {drift:.2f}pts"
            })
        else:
            report.append({"name": pilot.get("name", key), "status": "unchanged",
                           "qen_score": stored_qen})

    if corrected:
        with open(PILOTS_PATH, "w") as f:
            json.dump(pilots, f, indent=2, ensure_ascii=False)

    return jsonify({
        "status": "success",
        "processed": len(report),
        "corrected": corrected,
        "unchanged": len(report) - corrected,
        "report": report,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }), 200


# ── EVIDE — Evidentiary Registry ──────────────────────────────────────────────

EVIDE_PATH       = "/app/cognitivelogic/evide.json"
_EVIDE_LOCK_PATH = EVIDE_PATH + ".lock"

def _sha256(data: str) -> str:
    return "sha256:" + hashlib.sha256(data.encode("utf-8")).hexdigest()

def load_evide() -> dict:
    if not os.path.exists(EVIDE_PATH):
        return {
            "meta": {
                "version": "1.0",
                "protocol": "EVIDE/1.0",
                "created": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "updated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "total": 0,
                "glm_node": "it.cognitivelogic.node.01",
            },
            "entries": [],
        }
    with open(EVIDE_PATH, "r") as f:
        return json.load(f)

@app.route("/evide/chain", methods=["GET"])
def evide_chain():
    registry = load_evide()
    return jsonify(registry), 200

def _evide_append(entry_type: str, agent: str, operator_id: str,
                   input_obj, output_obj, qen_score=None, verdict: str = "PENDING") -> dict:
    """Append a chained, hash-linked entry to the EVIDE registry and return it.
    Shared by the /evide/register endpoint and every internal caller that writes
    a scored node to graph.json, so a node's qen_score is never persisted without
    a corresponding verifiable EVIDE entry."""
    input_payload  = json.dumps(input_obj,  sort_keys=True, ensure_ascii=False)
    output_payload = json.dumps(output_obj, sort_keys=True, ensure_ascii=False)

    try:
        Path(_EVIDE_LOCK_PATH).touch(exist_ok=True)
        with open(_EVIDE_LOCK_PATH, "r") as _lf:
            fcntl.flock(_lf, fcntl.LOCK_EX)
            try:
                registry = load_evide()
                entries  = registry.get("entries", [])
                seq      = len(entries) + 1

                prev_hash = None
                if entries:
                    prev_hash = _sha256(json.dumps(entries[-1], sort_keys=True, ensure_ascii=False))

                entry = {
                    "id":             f"evide-{seq:04d}",
                    "seq":            seq,
                    "timestamp":      datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "type":           entry_type,
                    "agent":          agent,
                    "operator_id":    operator_id,
                    "input_digest":   _sha256(input_payload),
                    "output_digest":  _sha256(output_payload),
                    "qen_score":      qen_score,
                    "verdict":        verdict,
                    "glm_node":       "it.cognitivelogic.node.01",
                    "prev_hash":      prev_hash,
                }
                entries.append(entry)
                registry["entries"] = entries
                registry.setdefault("meta", {})["total"]   = len(entries)
                registry["meta"]["updated"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

                with open(EVIDE_PATH, "w") as f:
                    json.dump(registry, f, indent=2, ensure_ascii=False)

                return entry
            finally:
                fcntl.flock(_lf, fcntl.LOCK_UN)
    except OSError as exc:
        # EVIDE_PATH's parent directory only exists on the deployed VPS. Degrade
        # to an unregistered entry (id=None) rather than failing the caller's
        # primary action (an audit save, a manual score entry) over the
        # evidentiary side-write — mirrors the existing best-effort graph.json
        # write pattern elsewhere in this file.
        app.logger.warning("EVIDE append failed for operator '%s': %s", operator_id, exc)
        return {
            "id": None, "seq": None, "type": entry_type, "agent": agent,
            "operator_id": operator_id, "qen_score": qen_score, "verdict": verdict,
            "input_digest": _sha256(input_payload), "output_digest": _sha256(output_payload),
            "glm_node": "it.cognitivelogic.node.01", "prev_hash": None,
            "error": "evide_store_unavailable",
        }

@app.route("/evide/register", methods=["POST"])
@limiter.limit("30 per minute;500 per day")
def evide_register():
    blocked = _require_trusted_origin()
    if blocked:
        return blocked

    data  = request.get_json() or {}
    entry = _evide_append(
        entry_type=data.get("type", "INFERENCE"),
        agent=data.get("agent", "unknown"),
        operator_id=data.get("operator_id", ""),
        input_obj=data.get("input", {}),
        output_obj=data.get("output", {}),
        qen_score=data.get("qen_score"),
        verdict=data.get("verdict", "PENDING"),
    )
    if entry.get("id") is None:
        return jsonify({"status": "error", "message": "EVIDE store unavailable"}), 503
    return jsonify({"status": "registered", "entry": entry}), 201


from orchestrator import register_orchestrator
register_orchestrator(app, limiter)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
