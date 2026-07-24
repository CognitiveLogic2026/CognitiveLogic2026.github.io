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
from datetime import datetime
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sovereign_engine import classify_risk as sovereign_classify_risk

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
    data = request.json
    if not data or "description" not in data:
        return jsonify({"error": "Campo description obbligatorio"}), 400
    descrizione     = data.get("description", "")
    entity_name     = data.get("entity_name", descrizione[:60])
    force_reanalyze = data.get("force", False)
    existing = check_duplicate(entity_name)
    if existing and not force_reanalyze:
        return jsonify({
            "duplicate":   True,
            "message":     "Analisi gia presente per " + entity_name + ". Usa force=true per rieseguire.",
            "timestamp":   existing.get("timestamp"),
            "cached_data": existing.get("data"),
            "analyses":    1 + len(existing.get("history", []))
        }), 200
    user_message = "Sistema AI da classificare: " + descrizione
    client = get_anthropic_client()
    if client is None:
        return jsonify({
            "status": "unavailable",
            "error": "external_provider_not_configured"
        }), 503
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=RISK_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        raw = response.content[0].text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            return jsonify({"error": "Risposta non valida dal modello"}), 500
        result = json.loads(m.group())
        allegato = result.get("allegato", "Nessuno")
        livello  = result.get("livello_rischio", "Minimo")
        score_map      = {"Vietato": 0.95, "Alto": 0.75, "Sorveglianza": 0.45, "Minimo": 0.15}
        gdpr_score_map = {"CRITICO": 0.90, "ALTO": 0.70, "MEDIO": 0.45, "BASSO": 0.15}
        gdpr_risk  = result.get("gdpr_risk", "BASSO")
        gdpr_score = gdpr_score_map.get(gdpr_risk, 0.15)
        ai_score   = score_map.get(livello, 0.15)
        final_score = round(max(ai_score, gdpr_score), 2)
        final_level = "HIGH" if final_score >= 0.70 else ("MEDIUM" if final_score >= 0.45 else "LOW")
        vs = float(result.get("vs", 50))
        va = float(result.get("va", 50))
        vt = float(result.get("vt", 50))
        qen_score = _qen(vs, va, vt)
        output = {
            "risk_level":        final_level,
            "risk_score":        final_score,
            "qen_score":         qen_score,
            "vs":                vs,
            "va":                va,
            "vt":                vt,
            "summary":           result.get("motivazione", ""),
            "why":               result.get("gdpr_motivazione", ""),
            "gdpr_risk":         gdpr_risk,
            "impact":            result.get("qen_impact", ""),
            "eu_classification": livello + " - Allegato " + allegato,
            "gaps":              result.get("articoli_rilevanti", []),
            "recommendations":   result.get("azioni_richieste", []),
            "decision":          livello
        }
        save_pilot(entity_name, output)
        return jsonify(output), 200
    except json.JSONDecodeError:
        return jsonify({"error": "Parsing fallito"}), 500
    except Exception:
        return jsonify({"error": "Errore interno del server"}), 500

@app.route("/gemini/qen-score", methods=["POST"])
@limiter.limit("10 per minute;100 per day")
def gemini_qen_score():
    blocked = _require_trusted_origin()
    if blocked:
        return blocked
    data   = request.get_json()
    name   = data.get("business_name", "")
    sector = data.get("sector", "")
    desc   = data.get("description", "")
    force_reanalyze = data.get("force", False)
    existing = check_duplicate(name)
    prompt = (
        "Analizza questa azienda e calcola il QEN Score.\n"
        "Nome: " + name + "\nSettore: " + sector + "\nDescrizione: " + desc + "\n\n"
        "Rispondi SOLO con JSON valido:\n"
        '{"qen_score": 0.00, "badge": "QEN VERIFIED", '
        '"vs": 0.00, "va": 0.00, "vt": 0.00, "sintesi": "testo"}'
    )
    if existing and not force_reanalyze:
        return jsonify({
            "duplicate":   True,
            "message":     "QEN Score gia presente per " + name + ". Usa force=true per rieseguire.",
            "timestamp":   existing.get("timestamp"),
            "cached_data": existing.get("data"),
            "analyses":    1 + len(existing.get("history", []))
        }), 200
    SIMPLE_SYSTEM = (
        "Sei un esperto QEN Score. Rispondi SOLO con JSON valido, nessun testo aggiuntivo.\n"
        "IMPORTANTE: vs, va, vt sono valori da 0 a 100 (non 0-10).\n"
        "Formula QEN: vs*0.40 + va*0.35 + vt*0.25\n"
        "Campi obbligatori: qen_score (0-100), badge (QEN VERIFIED o QEN UNVERIFIED), "
        "vs (0-100), va (0-100), vt (0-100), sintesi"
    )
    google_key = os.getenv("GOOGLE_API_KEY", "")
    try:
        if google_key:
            _GEMINI_MODELS = ["gemini-2.0-flash-lite", "gemini-2.5-flash", "gemini-2.0-flash"]
            raw = None
            provider = None
            for _model in _GEMINI_MODELS:
                try:
                    _resp = _requests.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/{_model}:generateContent",
                        params={"key": google_key},
                        json={
                            "system_instruction": {"parts": [{"text": SIMPLE_SYSTEM}]},
                            "contents": [{"parts": [{"text": prompt}]}],
                            "generationConfig": {"response_mime_type": "application/json"},
                        },
                        timeout=30,
                    )
                    _resp.raise_for_status()
                    raw = _resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    provider = _model
                    break
                except Exception as _me:
                    last_err = str(_me)
                    continue
            if raw is None:
                raise RuntimeError(f"Nessun modello Gemini disponibile: {last_err}")
        else:
            return jsonify({
                "status": "unavailable",
                "error": "external_provider_not_configured"
            }), 503

        raw = raw.replace("```json", "").replace("```", "").strip()
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            q = json.loads(m.group())
            vs = float(q.get("vs", 50))
            va = float(q.get("va", 50))
            vt = float(q.get("vt", 50))
            if max(vs, va, vt) <= 10:  # normalize 0-10 scale to 0-100
                vs, va, vt = vs * 10, va * 10, vt * 10
            q["vs"], q["va"], q["vt"] = vs, va, vt
            q["qen_score"] = _qen(vs, va, vt)
            q["provider"] = provider
            save_pilot(name, q)
            return jsonify({"status": "success", "qen": q})
        return jsonify({"status": "error", "error": "Risposta non valida dal modello"}), 500
    except Exception:
        return jsonify({"status": "error", "error": "Errore interno del server"}), 500

_COMPLIANCE_AUDIT_SYSTEM = (
    "You are QEN Compliance Auditor — an AI governance specialist operating under the "
    "Quantum Ethics Network (QEN) framework. Your role is to assess AI/biometric systems "
    "for regulatory risk, generate compliance findings, and produce governance recommendations.\n\n"
    "Core Framework:\n"
    "QEN Score = (Vs × 0.40) + (Va × 0.35) + (Vt × 0.25)\n"
    "Where:\n"
    "- Vs (Semantic Legality): Alignment with EU AI Act, GDPR, regulatory legitimacy [0–100]\n"
    "- Va (Accountability): Audit trail, human oversight, redress mechanisms [0–100]\n"
    "- Vt (Trust & Control): Data quality, transparency, reversibility, consent [0–100]\n\n"
    "Assessment Methodology:\n"
    "1. Risk Classification: Categorize system by EU AI Act Annex "
    "(Prohibited / High-Risk / Limited Risk / Minimal Risk)\n"
    "2. Vector Scoring: Evaluate each dimension independently using the scoring rubric\n"
    "3. Control Requirements: Map findings to mandatory controls\n"
    "4. Escalation Logic: Flag for immediate escalation if any vector < 30 OR system is Prohibited\n"
    "5. Recommendation: Produce actionable governance decisions "
    "(approve, conditional-approve, remediate, prohibit)\n\n"
    "You MUST output ONLY valid JSON with no additional text, following this exact schema:\n"
    '{"system_name":"string","risk_classification":"Prohibited|High-Risk|Limited-Risk|Minimal-Risk",'
    '"domain":"string","assessment_date":"ISO 8601 date",'
    '"scores":{"Vs":number,"Va":number,"Vt":number,"QEN_SCORE":number},'
    '"findings":[{"category":"string","severity":"Critical|High|Medium|Low",'
    '"issue":"string","evidence":"string","remediation":"string"}],'
    '"mandatory_controls":["string"],"escalation_flag":false,"escalation_reason":"string or null",'
    '"recommendation":"Approve|Conditional Approval|Remediation Required|Prohibit",'
    '"next_steps":["string"],"governance_owner":"string","review_date":"ISO 8601 date"}'
)

@app.route("/gemini/compliance-audit", methods=["POST"])
@limiter.limit("10 per minute;100 per day")
def gemini_compliance_audit():
    blocked = _require_trusted_origin()
    if blocked:
        return blocked
    data     = request.get_json() or {}
    name     = data.get("system_name", "Unnamed System")
    sys_type = data.get("system_type", "")
    domain   = data.get("domain", "")
    desc     = data.get("description", "")
    controls = data.get("controls", "(no controls documented)")
    if not desc:
        return jsonify({"error": "Campo description obbligatorio"}), 400
    today = datetime.utcnow().strftime("%Y-%m-%d")
    prompt = (
        f"Assess the following system under QEN framework v1.0:\n\n"
        f"System Name: {name}\nType: {sys_type}\nDomain: {domain}\n"
        f"Description: {desc}\nCurrent Controls: {controls}\n"
        f"Today's date: {today}\n\n"
        "Provide: 1) Risk classification (EU AI Act Annex) 2) QEN scores (Vs, Va, Vt) "
        "3) Findings (critical gaps) 4) Mandatory controls checklist "
        "5) Recommendation + next steps 6) Output as JSON only — no other text"
    )
    google_key = os.getenv("GOOGLE_API_KEY", "")
    try:
        raw = None
        provider = None
        if google_key:
            for _model in ["gemini-2.0-flash-lite", "gemini-2.5-flash", "gemini-2.0-flash"]:
                try:
                    _resp = _requests.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/{_model}:generateContent",
                        params={"key": google_key},
                        json={
                            "system_instruction": {"parts": [{"text": _COMPLIANCE_AUDIT_SYSTEM}]},
                            "contents": [{"parts": [{"text": prompt}]}],
                            "generationConfig": {"response_mime_type": "application/json"},
                        },
                        timeout=30,
                    )
                    _resp.raise_for_status()
                    raw = _resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    provider = _model
                    break
                except Exception:
                    continue
        if raw is None:
            return jsonify({
                "status": "unavailable",
                "error": "external_provider_not_configured"
            }), 503
        raw = raw.replace("```json", "").replace("```", "").strip()
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            q = json.loads(m.group())
            vs = float(q.get("scores", {}).get("Vs", 50))
            va = float(q.get("scores", {}).get("Va", 50))
            vt = float(q.get("scores", {}).get("Vt", 50))
            q.setdefault("scores", {})["QEN_SCORE"] = _qen(vs, va, vt)
            q["provider"] = provider
            return jsonify({"status": "success", "audit": q})
        return jsonify({"status": "error", "error": "Risposta non valida dal modello"}), 500
    except Exception:
        return jsonify({"status": "error", "error": "Errore interno del server"}), 500


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
