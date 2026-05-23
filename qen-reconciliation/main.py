import hashlib
import math
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import requests
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="QEN Reconciliation API", version="2.0.0")

QEN_BASE_SCORE = 75
THRESHOLD_GREEN = 0.15
THRESHOLD_YELLOW = 0.30
ADJUSTMENTS = {"ALIGNED": 0, "GREEN": -5, "YELLOW": -15, "RED": -30}

MOCK_SOURCES = {
    "distanza_media_fornitori_km": {"source": "OpenStreetMap", "reliability": 0.75, "value": 115.0},
    "biologico_certificato":       {"source": "ICEA",          "reliability": 0.90, "value": True},
    "percentuale_scarti":          {"source": "InfoCamere",    "reliability": 0.75, "value": 8.5},
    "consumo_kwh_anno":            {"source": "InfoCamere",    "reliability": 0.75, "value": 45000},
    "eu_ai_compliant":             {"source": "NANDO",         "reliability": 0.92, "value": True},
}


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin(math.radians(lat2 - lat1) / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


class OpenStreetMapAdapter:
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"
    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

    def geocode(self, comune: str) -> Optional[tuple[float, float]]:
        try:
            r = requests.get(
                self.NOMINATIM_URL,
                params={"q": f"{comune}, Italy", "format": "json", "limit": 1},
                headers={"User-Agent": "QENReconciliationAPI/2.0"},
                timeout=10,
            )
            results = r.json()
            if results:
                return float(results[0]["lat"]), float(results[0]["lon"])
        except Exception:
            pass
        return None

    def distanza_media_km(self, lat: float, lon: float, radius_m: int = 150_000) -> Optional[float]:
        query = (
            f"[out:json][timeout:25];"
            f"(node[\"shop\"=\"farm\"](around:{radius_m},{lat},{lon});"
            f"node[\"shop\"=\"butcher\"](around:{radius_m},{lat},{lon});"
            f"node[\"shop\"=\"organic\"](around:{radius_m},{lat},{lon}););"
            f"out center;"
        )
        try:
            r = requests.post(self.OVERPASS_URL, data={"data": query}, timeout=30)
            r.raise_for_status()
            elements = r.json().get("elements", [])
            distances = [
                _haversine(lat, lon, el["lat"], el["lon"])
                for el in elements if "lat" in el and "lon" in el
            ]
            return round(sum(distances) / len(distances), 1) if distances else None
        except Exception:
            return None


class ICEAAdapter:
    BASE_URL = "https://www.icea.bio/en/api/v1"

    def check_biologico(self, operator_id: str) -> Optional[bool]:
        api_key = os.getenv("ICEA_API_KEY")
        if not api_key:
            return None
        try:
            r = requests.get(
                f"{self.BASE_URL}/certification/{operator_id}",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10,
            )
            if r.status_code == 200:
                return bool(r.json().get("is_certified"))
        except Exception:
            pass
        return None


class InfoCamereAdapter:
    BASE_URL = "https://api.infocamere.it/telemaco/v1"

    def _get(self, path: str) -> Optional[Any]:
        api_key = os.getenv("INFOCAMERE_API_KEY")
        if not api_key:
            return None
        try:
            r = requests.get(
                f"{self.BASE_URL}/{path}",
                headers={"X-API-Key": api_key},
                timeout=10,
            )
            return r.json() if r.status_code == 200 else None
        except Exception:
            return None

    def get_percentuale_scarti(self, cf: str) -> Optional[float]:
        data = self._get(f"impresa/{cf}/scarti")
        return data.get("percentuale_scarti") if data else None

    def get_consumo_kwh(self, cf: str) -> Optional[float]:
        data = self._get(f"impresa/{cf}/energia")
        return data.get("consumo_kwh_anno") if data else None


class NANDOAdapter:
    # EU Commission NANDO database — publicly accessible
    BASE_URL = "https://ec.europa.eu/growth/tools-databases/nando/api/v1"

    def check_compliant(self, operator_name: str) -> Optional[bool]:
        try:
            r = requests.get(
                f"{self.BASE_URL}/notifiedbody",
                params={"keyword": operator_name, "country": "IT"},
                timeout=10,
            )
            if r.status_code == 200:
                return len(r.json().get("results", [])) > 0
        except Exception:
            pass
        return None


_osm = OpenStreetMapAdapter()
_icea = ICEAAdapter()
_infocamere = InfoCamereAdapter()
_nando = NANDOAdapter()


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
    source_type: str  # "live" | "mock"


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

    def _fetch(self, param: str, ctx: dict) -> tuple[Any, str, float, str]:
        """Try live adapters; fall back to mock on failure or missing credentials."""
        operator_id = ctx.get("operator_id", "")
        cf = ctx.get("codice_fiscale", "")
        comune = ctx.get("comune", "")
        lat, lon = ctx.get("lat"), ctx.get("lon")

        if param == "distanza_media_fornitori_km":
            coords: Optional[tuple[float, float]] = None
            if lat is not None and lon is not None:
                coords = (float(lat), float(lon))
            elif comune:
                coords = _osm.geocode(comune)
            if coords:
                val = _osm.distanza_media_km(*coords)
                if val is not None:
                    return val, "OpenStreetMap (live)", 0.85, "live"

        elif param == "biologico_certificato":
            val = _icea.check_biologico(operator_id or cf)
            if val is not None:
                return val, "ICEA (live)", 0.95, "live"

        elif param == "percentuale_scarti" and cf:
            val = _infocamere.get_percentuale_scarti(cf)
            if val is not None:
                return val, "InfoCamere (live)", 0.85, "live"

        elif param == "consumo_kwh_anno" and cf:
            val = _infocamere.get_consumo_kwh(cf)
            if val is not None:
                return val, "InfoCamere (live)", 0.85, "live"

        elif param == "eu_ai_compliant":
            val = _nando.check_compliant(operator_id)
            if val is not None:
                return val, "NANDO (live)", 0.95, "live"

        mock = MOCK_SOURCES.get(param)
        if mock:
            return mock["value"], mock["source"] + " (mock)", mock["reliability"], "mock"
        return None, "N/A", 0.0, "mock"

    def reconcile_parameter(self, param: str, declared: Any, ctx: dict) -> ParameterResult:
        verified, source, reliability, source_type = self._fetch(param, ctx)

        if verified is None:
            return ParameterResult(
                parameter=param, declared=declared, verified=None,
                source="N/A", reliability=0.0, discrepancy_pct=0.0,
                status="ALIGNED", adjustment=0, source_type="mock",
                message=f"✓ {param}: nessuna fonte esterna disponibile",
            )

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
            source_type=source_type,
        )


engine = QENEngine()


# ── Pydantic models ──────────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    operator_id: str
    operator_name: str
    declared_data: dict


class OperatorContext(BaseModel):
    codice_fiscale: str = ""
    comune: str = ""
    lat: Optional[float] = None
    lon: Optional[float] = None


class ReconcileRequest(BaseModel):
    operator_id: str
    operator_name: str
    declared_data: dict
    base_score: int = QEN_BASE_SCORE
    operator_context: OperatorContext = OperatorContext()


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "QEN Reconciliation API",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "sources": {
            "OpenStreetMap": "live (Overpass API)",
            "ICEA": "live" if os.getenv("ICEA_API_KEY") else "mock",
            "InfoCamere": "live" if os.getenv("INFOCAMERE_API_KEY") else "mock",
            "NANDO": "live (public)",
        },
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
    ctx = {"operator_id": req.operator_id, **req.operator_context.model_dump()}
    results = []
    total_adjustment = 0

    for param, value in req.declared_data.items():
        r = engine.reconcile_parameter(param, value, ctx)
        results.append({
            "parameter":       r.parameter,
            "declared":        r.declared,
            "verified":        r.verified,
            "source":          r.source,
            "source_type":     r.source_type,
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
