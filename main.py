# Copyright (c) 2026 Roberto Bob Malini - Cognitive Logic
# https://www.cognitivelogic.it
# Licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
import os
import json
import re
import requests as _requests
import anthropic
from datetime import datetime
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

@app.before_request
def handle_preflight():
    if request.method == 'OPTIONS':
        resp = app.make_response('')
        resp.status_code = 204
        return resp

@app.after_request
def add_cors(response):
    origin = request.headers.get('Origin', '')
    if 'cognitivelogic.it' in origin or not origin:
        response.headers['Access-Control-Allow-Origin'] = origin or '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-API-Key'
    return response

GRAPH_PATH   = "/app/cognitivelogic/graph.json"
PILOTS_PATH  = "/app/cognitivelogic/pilots.json"
ANTHROPIC_CLIENT = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def load_pilots():
    if not os.path.exists(PILOTS_PATH):
        return {}
    with open(PILOTS_PATH, "r") as f:
        return json.load(f)

def save_pilot(name, score_data):
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
    provided_key = request.headers.get("X-API-Key")
    if provided_key != os.getenv("COGNITIVE_API_KEY"):
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    data = request.json
    name   = data.get("system_name", "Unknown")
    social = data.get("social_impact", 0)
    env    = data.get("environmental_impact", 0)
    terr   = data.get("territorial_impact", 0)
    qen_score = round((social * 0.40) + (env * 0.35) + (terr * 0.25), 2)
    new_node = {"id": name, "type": "System", "qen": qen_score,
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

    new_node = {
        "id": nome, "type": "EntitaPilota", "label": nome,
        "settore": "HoReCa",
        "qen_score": {"vs": vs, "va": va, "vt": vt, "totale": qen},
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

    new_node = {
        "id": nome, "type": "EntitaPilota", "label": nome,
        "settore": "Balneare", "tipo": tipo,
        "qen_score": {"vs": vs, "va": va, "vt": vt, "totale": qen},
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
    provided_key = request.headers.get("X-API-Key")
    if provided_key != os.getenv("COGNITIVE_API_KEY"):
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    data    = request.json or {}
    nome    = (data.get("nome") or "Cliente").strip()
    settore = data.get("settore", "Generico")
    vs      = float(data.get("vs", 0))
    va      = float(data.get("va", 0))
    vt      = float(data.get("vt", 0))
    note    = data.get("note", "")
    qen     = round(vs * 0.40 + va * 0.35 + vt * 0.25, 2)

    score_data = {
        "qen_score": qen, "vs": vs, "va": va, "vt": vt,
        "settore": settore, "note": note,
    }
    save_pilot(nome, score_data)

    new_node = {
        "id": nome, "type": "EntitaPilota", "label": nome,
        "settore": settore, "note": note,
        "qen_score": {"vs": vs, "va": va, "vt": vt, "totale": qen},
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
def classify_risk():
    provided_key = request.headers.get("X-API-Key")
    if provided_key != os.getenv("COGNITIVE_API_KEY"):
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    data = request.json
    if not data or "descrizione" not in data:
        return jsonify({"status": "error", "message": "Campo descrizione obbligatorio"}), 400
    descrizione = data.get("descrizione", "")
    contesto    = data.get("contesto", "")
    settore     = data.get("settore", "")
    user_message = "Sistema: " + descrizione + " Contesto: " + contesto + " Settore: " + settore
    try:
        response = ANTHROPIC_CLIENT.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=RISK_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        raw = response.content[0].text.strip()
        if raw.startswith("`"):
            raw = raw.split("\n", 1)[1].rsplit("\n", 1)[0].strip().replace("`json", "").replace("```", "").strip()
        result = json.loads(raw)
        return jsonify({"status": "success", "sistema": descrizione[:80], "classificazione": result}), 200
    except json.JSONDecodeError:
        return jsonify({"status": "error", "message": "Parsing fallito", "raw": raw}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/copilot-analyze", methods=["POST"])
def copilot_analyze():
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
    try:
        response = ANTHROPIC_CLIENT.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=RISK_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        raw = response.content[0].text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            return jsonify({"error": "Nessun JSON trovato", "raw": raw[:200]}), 500
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
        qen_score = round((vs * 0.40) + (va * 0.35) + (vt * 0.25), 2)
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
        return jsonify({"error": "Parsing fallito", "raw": raw}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/gemini/qen-score", methods=["POST"])
def gemini_qen_score():
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
            msg = ANTHROPIC_CLIENT.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system=SIMPLE_SYSTEM,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = msg.content[0].text.strip()
            provider = "claude-haiku-fallback"

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
            q["qen_score"] = round((vs * 0.40) + (va * 0.35) + (vt * 0.25), 2)
            q["provider"] = provider
            save_pilot(name, q)
            return jsonify({"status": "success", "qen": q})
        return jsonify({"status": "error", "error": raw[:200]}), 500
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route("/copilot", methods=["GET"])
def copilot_ui():
    return send_file("copilot.html")

QEN_FORMULA_WEIGHTS = {"vs": 0.40, "va": 0.35, "vt": 0.25}
QEN_DRIFT_THRESHOLD = 0.5

@app.route("/reconcile/batch", methods=["POST"])
def reconcile_batch():
    provided_key = request.headers.get("X-API-Key")
    if provided_key != os.getenv("COGNITIVE_API_KEY"):
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

        expected_qen = round(float(vs) * 0.40 + float(va) * 0.35 + float(vt) * 0.25, 2)
        drift = abs(float(stored_qen) - expected_qen)

        if drift > QEN_DRIFT_THRESHOLD:
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

from orchestrator import register_orchestrator
register_orchestrator(app)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
