# Copyright (c) 2026 Roberto Bob Malini - Cognitive Logic
# https://www.cognitivelogic.it
# Licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="QEN Reconciliation API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

QEN_BASE_SCORE = 75
THRESHOLD_GREEN = 0.15
THRESHOLD_YELLOW = 0.30
ADJUSTMENTS = {"ALIGNED": 0, "GREEN": -5, "YELLOW": -15, "RED": -30}

ESCALATIONS_PATH = Path("/app/cognitivelogic/escalations.json")

ICEA_API_KEY = os.getenv("ICEA_API_KEY", "")
INFOCAMERE_API_KEY = os.getenv("INFOCAMERE_API_KEY", "")
SUPERVISOR_KEY = os.getenv("SUPERVISOR_KEY", "cna-supervisor-2026")

if not ICEA_API_KEY:
    logger.warning("ICEA_API_KEY not set — using mock data for biologico_certificato")
if not INFOCAMERE_API_KEY:
    logger.warning("INFOCAMERE_API_KEY not set — using mock data for InfoCamere sources")


def _fetch_icea(param: str) -> Any:
    """Stub for ICEA organic certification API. Replace body with real HTTP call when key is available."""
    if not ICEA_API_KEY:
        return True
    # Real call: GET https://api.icea.bio/v1/certification?key=ICEA_API_KEY&query=...
    return True


def _fetch_infocamere(param: str) -> Any:
    """Stub for InfoCamere registry API. Replace body with real HTTP call when key is available."""
    defaults = {"percentuale_scarti": 8.5, "consumo_kwh_anno": 45000}
    if not INFOCAMERE_API_KEY:
        return defaults.get(param)
    # Real call: GET https://api.infocamere.it/v2/registri?key=INFOCAMERE_API_KEY&param=...
    return defaults.get(param)


MOCK_SOURCES: dict[str, dict] = {
    "distanza_media_fornitori_km": {
        "source": "OpenStreetMap",
        "reliability": 0.75,
        "value_fn": lambda _: 115.0,
    },
    "biologico_certificato": {
        "source": "ICEA",
        "reliability": 0.90,
        "value_fn": lambda p: _fetch_icea(p),
    },
    "percentuale_scarti": {
        "source": "InfoCamere",
        "reliability": 0.75,
        "value_fn": lambda p: _fetch_infocamere(p),
    },
    "consumo_kwh_anno": {
        "source": "InfoCamere",
        "reliability": 0.75,
        "value_fn": lambda p: _fetch_infocamere(p),
    },
    "eu_ai_compliant": {
        "source": "NANDO",
        "reliability": 0.92,
        "value_fn": lambda _: True,
    },
}


@dataclass
class ParameterResult:
    parameter: str
    declared: Any
    verified: Any
    source: str
    reliability: float
    discrepancy_pct: float
    status: str
    adjustment: int
    message: str


class QENEngine:
    def _discrepancy(self, declared: Any, verified: Any) -> float:
        if isinstance(declared, bool) or isinstance(verified, bool):
            return 0.0 if declared == verified else 1.0
        if verified == 0:
            return 0.0
        return abs(float(declared) - float(verified)) / abs(float(verified))

    def _status(self, disc: float) -> str:
        if disc <= 0.0:
            return "ALIGNED"
        if disc <= THRESHOLD_GREEN:
            return "GREEN"
        if disc <= THRESHOLD_YELLOW:
            return "YELLOW"
        return "RED"

    def reconcile_parameter(self, param: str, declared: Any) -> ParameterResult:
        mock = MOCK_SOURCES.get(param)
        if not mock:
            return ParameterResult(
                parameter=param, declared=declared, verified=None,
                source="N/A", reliability=0.0, discrepancy_pct=0.0,
                status="ALIGNED", adjustment=0,
                message=f"✓ {param}: nessuna fonte esterna disponibile",
            )
        verified = mock["value_fn"](param)
        source = mock["source"]
        reliability = mock["reliability"]
        disc = self._discrepancy(declared, verified)
        status = self._status(disc)
        adj = ADJUSTMENTS[status]
        if status == "ALIGNED":
            msg = f"✓ {param}: verificato ({source})"
        elif status == "RED":
            msg = f"🛑 {disc * 100:.1f}% scostamento — fonte: {source}"
        elif status == "YELLOW":
            msg = f"⚠️ {disc * 100:.1f}% scostamento — fonte: {source}"
        else:
            msg = f"✅ {disc * 100:.1f}% entro tolleranza — fonte: {source}"
        return ParameterResult(
            parameter=param, declared=declared, verified=verified,
            source=source, reliability=reliability,
            discrepancy_pct=round(disc * 100, 2),
            status=status, adjustment=adj, message=msg,
        )


engine = QENEngine()


# ── Escalation persistence ────────────────────────────────────────────────────

def _load_escalations() -> dict:
    try:
        if ESCALATIONS_PATH.exists():
            return json.loads(ESCALATIONS_PATH.read_text())
    except Exception as exc:
        logger.error("Failed to load escalations: %s", exc)
    return {}


def _save_escalations(store: dict) -> None:
    try:
        ESCALATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
        ESCALATIONS_PATH.write_text(json.dumps(store, indent=2, ensure_ascii=False))
    except Exception as exc:
        logger.error("Failed to save escalations: %s", exc)


def _make_escalation_id(operator_id: str, param: str) -> str:
    key = f"{operator_id}:{param}:{datetime.utcnow().isoformat()}"
    return "ESC_" + hashlib.md5(key.encode()).hexdigest()[:8].upper()


def _save_escalations_from_reconcile(
    operator_id: str,
    operator_name: str,
    reconciliation_id: str,
    results: list[dict],
) -> None:
    store = _load_escalations()
    for r in results:
        if r["status"] not in ("RED", "YELLOW"):
            continue
        esc_id = _make_escalation_id(operator_id, r["parameter"])
        store[esc_id] = {
            "id": esc_id,
            "reconciliation_id": reconciliation_id,
            "operator_id": operator_id,
            "operator_name": operator_name,
            "parameter": r["parameter"],
            "declared": r["declared"],
            "verified": r["verified"],
            "source": r["source"],
            "discrepancy_pct": r["discrepancy_pct"],
            "status": r["status"],
            "escalation_status": "OPEN",
            "resolved_at": None,
            "resolved_by": None,
            "resolution_notes": None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    _save_escalations(store)


# ── Pydantic models ───────────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    operator_id: str
    operator_name: str
    declared_data: dict


class ReconcileRequest(BaseModel):
    operator_id: str
    operator_name: str
    declared_data: dict
    base_score: int = QEN_BASE_SCORE


class ResolveRequest(BaseModel):
    resolved_by: str
    resolution_notes: str = ""


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "QEN Reconciliation API",
        "version": "2.0.0",
        "icea_configured": bool(ICEA_API_KEY),
        "infocamere_configured": bool(INFOCAMERE_API_KEY),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.post("/api/ingest")
def ingest(req: IngestRequest):
    return {
        "status": "ingested",
        "operator_id": req.operator_id,
        "operator_name": req.operator_name,
        "parameters_received": list(req.declared_data.keys()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.post("/api/reconcile")
def reconcile(req: ReconcileRequest):
    results = []
    total_adjustment = 0

    for param, value in req.declared_data.items():
        r = engine.reconcile_parameter(param, value)
        results.append({
            "parameter":       r.parameter,
            "declared":        r.declared,
            "verified":        r.verified,
            "source":          r.source,
            "reliability":     r.reliability,
            "discrepancy_pct": r.discrepancy_pct,
            "status":          r.status,
            "adjustment":      r.adjustment,
            "message":         r.message,
        })
        total_adjustment += r.adjustment

    score_after = max(0, req.base_score + total_adjustment)
    rec_id = "REC_" + hashlib.md5(
        f"{req.operator_id}{datetime.utcnow().isoformat()}".encode()
    ).hexdigest()[:8].upper()

    _save_escalations_from_reconcile(
        req.operator_id, req.operator_name, rec_id, results
    )

    return {
        "reconciliation_id": rec_id,
        "operator_id":       req.operator_id,
        "operator_name":     req.operator_name,
        "parameter_results": results,
        "qen_score": {
            "before":     req.base_score,
            "after":      score_after,
            "adjustment": total_adjustment,
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/api/escalations")
def list_escalations(status: Optional[str] = None):
    store = _load_escalations()
    items = list(store.values())
    if status:
        items = [e for e in items if e.get("escalation_status") == status.upper()]
    items.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    open_count = sum(1 for e in store.values() if e.get("escalation_status") == "OPEN")
    resolved_count = len(store) - open_count
    red_count = sum(1 for e in items if e.get("status") == "RED")
    yellow_count = sum(1 for e in items if e.get("status") == "YELLOW")
    return {
        "total": len(items),
        "stats": {
            "open": open_count,
            "resolved": resolved_count,
            "red": red_count,
            "yellow": yellow_count,
        },
        "escalations": items,
    }


@app.post("/api/escalations/{esc_id}/resolve")
def resolve_escalation(
    esc_id: str,
    req: ResolveRequest,
    x_supervisor_key: Optional[str] = Header(None),
):
    if x_supervisor_key != SUPERVISOR_KEY:
        raise HTTPException(status_code=403, detail="Chiave supervisore non valida")
    store = _load_escalations()
    if esc_id not in store:
        raise HTTPException(status_code=404, detail=f"Escalation {esc_id} non trovata")
    esc = store[esc_id]
    if esc["escalation_status"] == "RESOLVED":
        raise HTTPException(status_code=409, detail="Escalation già risolta")
    esc["escalation_status"] = "RESOLVED"
    esc["resolved_at"] = datetime.utcnow().isoformat() + "Z"
    esc["resolved_by"] = req.resolved_by
    esc["resolution_notes"] = req.resolution_notes
    store[esc_id] = esc
    _save_escalations(store)
    return {"status": "resolved", "escalation": esc}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
