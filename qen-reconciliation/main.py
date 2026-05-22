import hashlib
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="QEN Reconciliation API", version="1.0.0")

QEN_BASE_SCORE = 75

# CNA Bolkestein 2027 thresholds
THRESHOLD_GREEN = 0.15   # ≤15%  → -5 pts
THRESHOLD_YELLOW = 0.30  # ≤30%  → -15 pts
# >30%                           → RED -30 pts

ADJUSTMENTS = {"ALIGNED": 0, "GREEN": -5, "YELLOW": -15, "RED": -30}

# Mock verified sources (production: replace with real API wrappers)
MOCK_SOURCES = {
    "distanza_media_fornitori_km": {"source": "OpenStreetMap", "reliability": 0.75, "value": 115.0},
    "biologico_certificato":       {"source": "ICEA",          "reliability": 0.90, "value": True},
    "percentuale_scarti":          {"source": "InfoCamere",    "reliability": 0.75, "value": 8.5},
    "consumo_kwh_anno":            {"source": "InfoCamere",    "reliability": 0.75, "value": 45000},
    "eu_ai_compliant":             {"source": "NANDO",         "reliability": 0.92, "value": True},
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
        verified = mock["value"]
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


# ── Pydantic models ──────────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    operator_id: str
    operator_name: str
    declared_data: dict


class ReconcileRequest(BaseModel):
    operator_id: str
    operator_name: str
    declared_data: dict
    base_score: int = QEN_BASE_SCORE


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "QEN Reconciliation API",
        "version": "1.0.0",
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
    ).hexdigest()[:8]

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
