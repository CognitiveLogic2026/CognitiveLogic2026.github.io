# Copyright (c) 2026 Roberto Bob Malini - Cognitive Logic
# Modulo wizard PMI: calcolo deterministico pesato + persistenza Redis a tre namespace.
# Registrato su main.py con lo stesso pattern di orchestrator.py (register_orchestrator).
import os
import json
from datetime import datetime

import redis as _redis_lib
from flask import request, jsonify

_redis_client = None

_TWELVE_MONTHS_SECONDS = 60 * 60 * 24 * 365
_DISCLAIMER_TTL_SECONDS = 60 * 60  # sessione breve

_AREA_WEIGHTS = {"A": 0.40, "B": 0.35, "C": 0.25}


def _get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = _redis_lib.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    return _redis_client


def _area_score_0_100(values):
    if not values:
        return None
    avg = sum(values) / len(values)
    return round((avg / 3.0) * 100, 2)


def _qen_wizard(a_score, b_score, c_score):
    return round(
        a_score * _AREA_WEIGHTS["A"] + b_score * _AREA_WEIGHTS["B"] + c_score * _AREA_WEIGHTS["C"], 2
    )


def _verdict_for_qen(score):
    if score < 60:
        return "NON_COMPLIANT"
    if score < 70:
        return "REVIEW_REQUIRED"
    return "COMPLIANT"


def register_wizard(app, limiter=None, require_trusted_origin=None):
    _lim = limiter.limit if limiter else lambda _rule: (lambda f: f)
    _origin_check = require_trusted_origin if require_trusted_origin else (lambda: None)

    @app.route("/gemini/compliance-audit/wizard/disclaimer", methods=["POST"])
    @_lim("30 per minute;300 per day")
    def wizard_disclaimer():
        blocked = _origin_check()
        if blocked:
            return blocked
        data = request.get_json() or {}
        session_id = (data.get("sessionId") or "").strip()
        if not session_id:
            return jsonify({"error": "sessionId obbligatorio"}), 400
        if not bool(data.get("consented", False)):
            return jsonify({"error": "consenso non fornito"}), 400
        payload = {"consented": True, "timestamp": datetime.utcnow().isoformat() + "Z"}
        try:
            _get_redis().setex(f"qen:disclaimer:{session_id}", _DISCLAIMER_TTL_SECONDS, json.dumps(payload))
        except Exception as e:
            return jsonify({"error": "persistenza non riuscita", "detail": str(e)}), 500
        return jsonify({"status": "ok"}), 200

    @app.route("/gemini/compliance-audit/wizard/submit", methods=["POST"])
    @_lim("10 per minute;100 per day")
    def wizard_submit():
        blocked = _origin_check()
        if blocked:
            return blocked
        data = request.get_json() or {}
        session_id = (data.get("sessionId") or "").strip()
        answers = data.get("answers", [])
        if not session_id or not answers:
            return jsonify({"error": "sessionId e answers obbligatori"}), 400

        try:
            if not _get_redis().exists(f"qen:disclaimer:{session_id}"):
                return jsonify({"error": "disclaimer non confermato per questa sessione"}), 403
        except Exception as e:
            return jsonify({"error": "verifica disclaimer non riuscita", "detail": str(e)}), 500

        area_values = {"A": [], "B": [], "C": []}
        for a in answers:
            area = a.get("area")
            value = a.get("value")
            if area in area_values and isinstance(value, (int, float)) and 0 <= value <= 3:
                area_values[area].append(value)

        a_score = _area_score_0_100(area_values["A"])
        b_score = _area_score_0_100(area_values["B"])
        c_score = _area_score_0_100(area_values["C"])
        if a_score is None or b_score is None or c_score is None:
            return jsonify({"error": "risposte incomplete, servono valori per le aree A, B, C"}), 400

        qen_total = _qen_wizard(a_score, b_score, c_score)
        verdict = _verdict_for_qen(qen_total)
        now = datetime.utcnow().isoformat() + "Z"

        assessment_payload = {
            "sessionId": session_id,
            "answers": answers,
            "area_scores": {"A": a_score, "B": b_score, "C": c_score},
            "qen_score": qen_total,
            "verdict": verdict,
            "timestamp": now,
        }
        aggregate_payload = {
            "area_scores": {"A": a_score, "B": b_score, "C": c_score},
            "qen_score": qen_total,
            "verdict": verdict,
            "timestamp": now,
        }

        try:
            rc = _get_redis()
            rc.setex(f"qen:assessment:{session_id}", _TWELVE_MONTHS_SECONDS, json.dumps(assessment_payload))
            rc.set(f"qen:assessment:aggregate:{session_id}", json.dumps(aggregate_payload))
        except Exception as e:
            return jsonify({"error": "persistenza non riuscita", "detail": str(e)}), 500

        webhook_url = os.getenv("QEN_WEBHOOK_URL", "")
        if webhook_url:
            try:
                import requests as _wh_requests
                _wh_requests.post(
                    webhook_url,
                    json={
                        "event": "qen.assessment.completed",
                        "sessionId": session_id,
                        "qen_score": qen_total,
                        "verdict": verdict,
                    },
                    timeout=2,
                )
            except Exception:
                pass  # best-effort, non bloccante

        return jsonify({
            "status": "ok",
            "qen_score": qen_total,
            "verdict": verdict,
            "area_scores": {"A": a_score, "B": b_score, "C": c_score},
        }), 200
