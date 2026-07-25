# Copyright (c) 2026 Roberto Bob Malini - Cognitive Logic
# https://www.cognitivelogic.it
# Licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
import hashlib
import hmac
import json
import logging
import math
import os
import smtplib
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta, UTC
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="QEN Reconciliation API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cognitivelogic.it", "https://www.cognitivelogic.it", "https://api.cognitivelogic.it"],
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
SUPERVISOR_KEY = os.getenv("SUPERVISOR_KEY")
if not SUPERVISOR_KEY:
    raise RuntimeError("SUPERVISOR_KEY environment variable is required")

# ── SMTP / email config ───────────────────────────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
ALERT_EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM", SMTP_USER)
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO", "")

_EMAIL_ENABLED = bool(SMTP_HOST and SMTP_USER and SMTP_PASS and ALERT_EMAIL_TO)
if not _EMAIL_ENABLED:
    logger.warning("SMTP not fully configured — email alerts disabled (set SMTP_HOST, SMTP_USER, SMTP_PASS, ALERT_EMAIL_TO)")

# ── SLA config ────────────────────────────────────────────────────────────────
SLA_HOURS: dict[str, int] = {"RED": 24, "YELLOW": 72}

if not ICEA_API_KEY:
    logger.warning("ICEA_API_KEY not set — mock fallback active for biologico_certificato")
if not INFOCAMERE_API_KEY:
    logger.warning("INFOCAMERE_API_KEY not set — mock fallback active for InfoCamere sources")

_CACHE_TTL = 3600  # seconds
_SOURCE_CACHE: dict = {}
_NOMINATIM_LOCK = threading.Lock()
_NOMINATIM_LAST: float = 0.0

_INFOCAMERE_DEFAULTS: dict = {"percentuale_scarti": 8.5, "consumo_kwh_anno": 45000.0}

# Reliability ceiling applied when a source falls back to a mock/default value
# instead of an actual live lookup. A source's nominal "reliability" describes
# how much to trust *that source when it actually answers* — it must not carry
# over unchanged to a hardcoded fallback, or a mock value ends up reconciled
# with the same confidence as a verified one.
MOCK_RELIABILITY_CAP = 0.3


# ── Email notifications ───────────────────────────────────────────────────────

def _build_red_alert_email(esc: dict) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[CNA ALERT] Escalation RED — {esc['operator_name']} / {esc['parameter']}"
    msg["From"] = ALERT_EMAIL_FROM
    msg["To"] = ALERT_EMAIL_TO

    deadline = esc.get("sla_deadline", "N/A")
    plain = (
        f"ESCALATION RED APERTA\n\n"
        f"ID:           {esc['id']}\n"
        f"Operatore:    {esc['operator_name']} ({esc['operator_id']})\n"
        f"Parametro:    {esc['parameter']}\n"
        f"Dichiarato:   {esc['declared']}\n"
        f"Verificato:   {esc['verified']}\n"
        f"Scostamento:  {esc['discrepancy_pct']}%\n"
        f"Fonte:        {esc['source']}\n"
        f"Timestamp:    {esc['timestamp']}\n"
        f"SLA Deadline: {deadline} (entro 24h)\n\n"
        f"Accedi alla dashboard supervisore per risolvere questa escalation.\n"
        f"https://cognitivelogic.it/escalation.html\n"
    )
    html = f"""<!DOCTYPE html>
<html lang="it"><head><meta charset="UTF-8"></head>
<body style="font-family:monospace;background:#05080f;color:#ccd4ef;padding:2rem;">
  <div style="max-width:560px;margin:0 auto;border:1px solid #181d30;padding:2rem;">
    <p style="font-size:0.65rem;letter-spacing:0.3em;text-transform:uppercase;color:#c8a84b;margin-bottom:1rem;">
      CNA Bolkestein 2027 · QEN Reconciliation
    </p>
    <h1 style="color:#ff5f57;font-size:1.4rem;margin-bottom:1.5rem;">
      &#x1F6D1; Escalation RED Aperta
    </h1>
    <table style="width:100%;border-collapse:collapse;font-size:0.85rem;">
      <tr><td style="color:#8892b5;padding:0.35rem 0;width:140px;">ID</td>
          <td style="color:#ccd4ef;">{esc['id']}</td></tr>
      <tr><td style="color:#8892b5;padding:0.35rem 0;">Operatore</td>
          <td style="color:#ccd4ef;font-weight:bold;">{esc['operator_name']}</td></tr>
      <tr><td style="color:#8892b5;padding:0.35rem 0;">Parametro</td>
          <td style="color:#ccd4ef;">{esc['parameter']}</td></tr>
      <tr><td style="color:#8892b5;padding:0.35rem 0;">Dichiarato</td>
          <td style="color:#ccd4ef;">{esc['declared']}</td></tr>
      <tr><td style="color:#8892b5;padding:0.35rem 0;">Verificato</td>
          <td style="color:#ccd4ef;">{esc['verified']}</td></tr>
      <tr><td style="color:#8892b5;padding:0.35rem 0;">Scostamento</td>
          <td style="color:#ff5f57;font-weight:bold;">{esc['discrepancy_pct']}%</td></tr>
      <tr><td style="color:#8892b5;padding:0.35rem 0;">Fonte</td>
          <td style="color:#ccd4ef;">{esc['source']}</td></tr>
      <tr><td style="color:#8892b5;padding:0.35rem 0;">SLA Deadline</td>
          <td style="color:#ffd166;font-weight:bold;">{deadline}</td></tr>
    </table>
    <div style="margin-top:1.5rem;padding:1rem;background:#0a0d1a;border-left:3px solid #ff5f57;">
      <p style="font-size:0.8rem;color:#8892b5;margin-bottom:0.5rem;">
        Questa escalation deve essere risolta entro 24 ore dalla creazione.
      </p>
      <a href="https://cognitivelogic.it/escalation.html"
         style="color:#3dffa0;font-size:0.85rem;">
        → Apri Dashboard Supervisore
      </a>
    </div>
  </div>
</body></html>"""

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))
    return msg


def _send_red_alert_email(esc: dict) -> None:
    if not _EMAIL_ENABLED:
        return

    def _send():
        try:
            msg = _build_red_alert_email(esc)
            if SMTP_PORT == 465:
                with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15) as srv:
                    srv.login(SMTP_USER, SMTP_PASS)
                    srv.sendmail(ALERT_EMAIL_FROM, ALERT_EMAIL_TO.split(","), msg.as_string())
            else:
                with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as srv:
                    srv.ehlo()
                    srv.starttls()
                    srv.login(SMTP_USER, SMTP_PASS)
                    srv.sendmail(ALERT_EMAIL_FROM, ALERT_EMAIL_TO.split(","), msg.as_string())
            logger.info("RED alert email sent for %s (%s)", esc["id"], esc["operator_name"])
        except Exception as exc:
            logger.error("Failed to send RED alert email for %s: %s", esc["id"], exc)

    threading.Thread(target=_send, daemon=True).start()


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _http_get(url: str, timeout: int = 10) -> Any:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "CognitiveLogic-QEN/2.0 (https://cognitivelogic.it)"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _http_post_form(url: str, payload: bytes, timeout: int = 20) -> Any:
    req = urllib.request.Request(
        url, data=payload,
        headers={"User-Agent": "CognitiveLogic-QEN/2.0 (https://cognitivelogic.it)"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _cache_get(key: str) -> Any:
    entry = _SOURCE_CACHE.get(key)
    if entry and (time.monotonic() - entry["ts"] < _CACHE_TTL):
        return entry["value"]
    return None


def _cache_set(key: str, value: Any) -> None:
    _SOURCE_CACHE[key] = {"value": value, "ts": time.monotonic()}


# ── ICEA integration ──────────────────────────────────────────────────────────

def _fetch_icea(param: str, context: dict) -> tuple[bool, bool]:
    """
    Verify organic certification via ICEA API.
    Requires ICEA_API_KEY; degrades gracefully to True when absent or on error.
    Returns (value, verified) — verified is False whenever the value comes from
    the mock fallback rather than a live ICEA response.
    """
    operator_id = context.get("operator_id", "")
    cache_key = f"icea:{operator_id}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return bool(cached), True

    if not ICEA_API_KEY:
        return True, False

    url = "https://api.icea.bio/v1/certification?" + urllib.parse.urlencode({
        "key": ICEA_API_KEY,
        "query": operator_id,
    })
    try:
        data = _http_get(url)
        # Tolerate multiple response shapes from the ICEA endpoint
        result = bool(
            data.get("certified")
            or data.get("attivo")
            or data.get("valid")
            or data.get("stato") == "attivo"
        )
        _cache_set(cache_key, result)
        logger.info("ICEA: operator '%s' certified=%s", operator_id, result)
        return result, True
    except Exception as exc:
        logger.warning("ICEA API error for '%s': %s — using mock fallback", operator_id, exc)
        return True, False


# ── InfoCamere integration ────────────────────────────────────────────────────

def _fetch_infocamere(param: str, context: dict) -> tuple[Any, bool]:
    """
    Fetch a sustainability parameter from the InfoCamere business registry.
    Requires INFOCAMERE_API_KEY; degrades gracefully to sector defaults on error.
    Returns (value, verified) — verified is False whenever the value is a
    sector default rather than a live InfoCamere response.
    """
    operator_id = context.get("operator_id", "")
    cache_key = f"infocamere:{operator_id}:{param}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached, True

    if not INFOCAMERE_API_KEY:
        return _INFOCAMERE_DEFAULTS.get(param), False

    url = "https://api.infocamere.it/v2/registri?" + urllib.parse.urlencode({
        "key": INFOCAMERE_API_KEY,
        "cf": operator_id,
        "param": param,
    })
    try:
        data = _http_get(url)
        raw = data.get(param) or data.get("value") or data.get("valore")
        if raw is None:
            logger.warning("InfoCamere: '%s' missing in response for '%s'", param, operator_id)
            return _INFOCAMERE_DEFAULTS.get(param), False
        value = float(raw)
        _cache_set(cache_key, value)
        logger.info("InfoCamere: '%s' for operator '%s' = %.2f", param, operator_id, value)
        return value, True
    except Exception as exc:
        logger.warning("InfoCamere API error for '%s'/'%s': %s — using sector default", operator_id, param, exc)
        return _INFOCAMERE_DEFAULTS.get(param), False


# ── OpenStreetMap integration ─────────────────────────────────────────────────

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _nominatim_geocode(query: str) -> Optional[tuple]:
    """
    Return (lat, lon) for an Italian location query.
    Enforces the Nominatim 1 req/s policy via a module-level lock and timestamp.
    """
    global _NOMINATIM_LAST
    with _NOMINATIM_LOCK:
        elapsed = time.monotonic() - _NOMINATIM_LAST
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
        _NOMINATIM_LAST = time.monotonic()

    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({
        "q": query,
        "format": "json",
        "limit": 1,
        "countrycodes": "it",
    })
    try:
        data = _http_get(url)
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as exc:
        logger.warning("Nominatim geocoding failed for '%s': %s", query, exc)
    return None


def _overpass_suppliers(lat: float, lon: float) -> list:
    """
    Find farm and cooperative nodes near (lat, lon) using the Overpass API.
    Bounding box: ±1° lat (~111 km), ±1.5° lon (~100 km at 45° N).
    """
    s, n, w, e = lat - 1.0, lat + 1.0, lon - 1.5, lon + 1.5
    bb = f"{s},{w},{n},{e}"
    query = (
        "[out:json][timeout:20];"
        "("
        f'node["landuse"="farmyard"]({bb});'
        f'node["office"="cooperative"]({bb});'
        f'node["shop"="farm"]({bb});'
        f'node["amenity"="marketplace"]["marketplace"~"farmers",i]({bb});'
        ");"
        "out;"
    )
    try:
        data = _http_post_form(
            "https://overpass-api.de/api/interpreter",
            urllib.parse.urlencode({"data": query}).encode(),
        )
        return [
            (float(el["lat"]), float(el["lon"]))
            for el in data.get("elements", [])
            if "lat" in el and "lon" in el
        ][:50]
    except Exception as exc:
        logger.warning("Overpass API failed: %s", exc)
    return []


def _fetch_osm_distance(context: dict) -> tuple[float, bool]:
    """
    Compute average km from operator to nearby agricultural suppliers via OSM.
    Falls back to 115.0 km (Italian HoReCa sector benchmark) when geocoding
    or Overpass queries return no usable data.
    Returns (value, verified) — verified is False whenever the fallback
    benchmark distance is used instead of a computed value.
    """
    operator_name = context.get("operator_name", "")
    fallback = 115.0

    if not operator_name:
        return fallback, False

    cache_key = f"osm:{operator_name}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return float(cached), True

    coords = _nominatim_geocode(f"{operator_name}, Italia")
    if not coords:
        logger.warning("OSM: geocoding failed for '%s', using fallback %.1f km", operator_name, fallback)
        return fallback, False

    lat, lon = coords
    suppliers = _overpass_suppliers(lat, lon)
    if not suppliers:
        logger.warning("OSM: no supplier nodes near '%s' (%.4f, %.4f), using fallback", operator_name, lat, lon)
        return fallback, False

    distances = [_haversine(lat, lon, slat, slon) for slat, slon in suppliers]
    avg = round(sum(distances) / len(distances), 1)
    _cache_set(cache_key, avg)
    logger.info("OSM: avg supplier distance for '%s' = %.1f km (%d nodes)", operator_name, avg, len(suppliers))
    return avg, True


# ── Source registry ───────────────────────────────────────────────────────────

SOURCES: dict = {
    "distanza_media_fornitori_km": {
        "source": "OpenStreetMap",
        "reliability": 0.75,
        "value_fn": lambda p, ctx: _fetch_osm_distance(ctx),
    },
    "biologico_certificato": {
        "source": "ICEA",
        "reliability": 0.90,
        "value_fn": lambda p, ctx: _fetch_icea(p, ctx),
    },
    "percentuale_scarti": {
        "source": "InfoCamere",
        "reliability": 0.75,
        "value_fn": lambda p, ctx: _fetch_infocamere(p, ctx),
    },
    "consumo_kwh_anno": {
        "source": "InfoCamere",
        "reliability": 0.75,
        "value_fn": lambda p, ctx: _fetch_infocamere(p, ctx),
    },
    "eu_ai_compliant": {
        "source": "NANDO",
        "reliability": 0.92,
        # NANDO integration is not implemented yet (cfr. VALIDATION_STATUS.md) —
        # this always returns the mock value, never a live lookup.
        "value_fn": lambda p, ctx: (True, False),
    },
}


@dataclass
class ParameterResult:
    parameter: str
    declared: Any
    verified: Any
    source: str
    reliability: float
    verified_source: bool
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

    def reconcile_parameter(
        self, param: str, declared: Any, context: Optional[dict] = None
    ) -> ParameterResult:
        ctx = context or {}
        source_def = SOURCES.get(param)
        if not source_def:
            return ParameterResult(
                parameter=param, declared=declared, verified=None,
                source="N/A", reliability=0.0, verified_source=False,
                discrepancy_pct=0.0,
                status="ALIGNED", adjustment=0,
                message=f"✓ {param}: nessuna fonte esterna disponibile",
            )
        verified, verified_source = source_def["value_fn"](param, ctx)
        source = source_def["source"]
        reliability = source_def["reliability"]
        if not verified_source:
            # A mock/fallback value must not carry the source's nominal
            # reliability — cap it so downstream consumers can see the
            # confidence was degraded, not just that a value exists.
            reliability = min(reliability, MOCK_RELIABILITY_CAP)
        disc = self._discrepancy(declared, verified)
        status = self._status(disc)
        adj = ADJUSTMENTS[status]
        mock_tag = "" if verified_source else " [MOCK — fonte non raggiungibile/non configurata]"
        if status == "ALIGNED" and verified_source:
            msg = f"✓ {param}: verificato ({source})"
        elif status == "ALIGNED":
            msg = f"✓ {param}: dichiarato coerente col default ({source}){mock_tag}"
        elif status == "RED":
            msg = f"🛑 {disc * 100:.1f}% scostamento — fonte: {source}{mock_tag}"
        elif status == "YELLOW":
            msg = f"⚠️ {disc * 100:.1f}% scostamento — fonte: {source}{mock_tag}"
        else:
            msg = f"✅ {disc * 100:.1f}% entro tolleranza — fonte: {source}{mock_tag}"
        return ParameterResult(
            parameter=param, declared=declared, verified=verified,
            source=source, reliability=reliability, verified_source=verified_source,
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
    key = f"{operator_id}:{param}:{datetime.now(UTC).replace(tzinfo=None).isoformat()}"
    return "ESC_" + hashlib.md5(key.encode()).hexdigest()[:8].upper()


def _save_escalations_from_reconcile(
    operator_id: str,
    operator_name: str,
    reconciliation_id: str,
    results: list,
) -> None:
    store = _load_escalations()
    new_red: list[dict] = []

    for r in results:
        if r["status"] not in ("RED", "YELLOW"):
            continue
        esc_id = _make_escalation_id(operator_id, r["parameter"])
        now = datetime.now(timezone.utc)
        sla_h = SLA_HOURS[r["status"]]
        esc = {
            "id": esc_id,
            "reconciliation_id": reconciliation_id,
            "operator_id": operator_id,
            "operator_name": operator_name,
            "parameter": r["parameter"],
            "declared": r["declared"],
            "verified": r["verified"],
            "source": r["source"],
            "reliability": r["reliability"],
            "verified_source": r["verified_source"],
            "discrepancy_pct": r["discrepancy_pct"],
            "status": r["status"],
            "escalation_status": "OPEN",
            "resolved_at": None,
            "resolved_by": None,
            "resolution_notes": None,
            "timestamp": now.isoformat(),
            "sla_hours": sla_h,
            "sla_deadline": (now + timedelta(hours=sla_h)).isoformat(),
            "email_sent": False,
        }
        store[esc_id] = esc
        if r["status"] == "RED":
            new_red.append(esc)

    _save_escalations(store)

    # Fire emails after saving so IDs are already persisted
    for esc in new_red:
        _send_red_alert_email(esc)
        # Mark email_sent without re-reading the full store
        store[esc["id"]]["email_sent"] = True
    if new_red:
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
        "sources": {
            "icea": {"configured": bool(ICEA_API_KEY), "fallback": "mock_true"},
            "infocamere": {"configured": bool(INFOCAMERE_API_KEY), "fallback": "sector_defaults"},
            "openstreetmap": {"configured": True, "fallback": "115.0_km"},
            "nando": {"configured": True, "fallback": "mock_true"},
        },
        "notifications": {
            "email_alerts": _EMAIL_ENABLED,
            "smtp_host": SMTP_HOST or None,
        },
        "sla": {"RED_hours": SLA_HOURS["RED"], "YELLOW_hours": SLA_HOURS["YELLOW"]},
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }


@app.post("/api/ingest")
def ingest(req: IngestRequest):
    return {
        "status": "ingested",
        "operator_id": req.operator_id,
        "operator_name": req.operator_name,
        "parameters_received": list(req.declared_data.keys()),
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }


@app.post("/api/reconcile")
def reconcile(req: ReconcileRequest):
    context = {"operator_id": req.operator_id, "operator_name": req.operator_name}
    results = []
    total_adjustment = 0

    for param, value in req.declared_data.items():
        r = engine.reconcile_parameter(param, value, context)
        results.append({
            "parameter":       r.parameter,
            "declared":        r.declared,
            "verified":        r.verified,
            "source":          r.source,
            "reliability":     r.reliability,
            "verified_source": r.verified_source,
            "discrepancy_pct": r.discrepancy_pct,
            "status":          r.status,
            "adjustment":      r.adjustment,
            "message":         r.message,
        })
        total_adjustment += r.adjustment

    score_after = max(0, req.base_score + total_adjustment)
    rec_id = "REC_" + hashlib.md5(
        f"{req.operator_id}{datetime.now(UTC).replace(tzinfo=None).isoformat()}".encode()
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
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }


def _enrich_sla(esc: dict) -> dict:
    """Add computed sla_breached / sla_hours_elapsed fields without mutating the store."""
    e = dict(esc)
    if e.get("escalation_status") == "RESOLVED" or not e.get("sla_deadline"):
        e["sla_breached"] = False
        e["sla_hours_elapsed"] = None
        return e
    try:
        deadline = datetime.fromisoformat(e["sla_deadline"])
        now = datetime.now(timezone.utc)
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        elapsed_h = round((now - datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))).total_seconds() / 3600, 1)
        e["sla_breached"] = now > deadline
        e["sla_hours_elapsed"] = elapsed_h
    except Exception:
        e["sla_breached"] = False
        e["sla_hours_elapsed"] = None
    return e


@app.get("/api/escalations")
def list_escalations(status: Optional[str] = None):
    store = _load_escalations()
    items = [_enrich_sla(e) for e in store.values()]
    if status:
        items = [e for e in items if e.get("escalation_status") == status.upper()]
    items.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    open_count = sum(1 for e in store.values() if e.get("escalation_status") == "OPEN")
    resolved_count = len(store) - open_count
    red_count = sum(1 for e in items if e.get("status") == "RED")
    yellow_count = sum(1 for e in items if e.get("status") == "YELLOW")
    sla_breach_count = sum(1 for e in items if e.get("sla_breached"))
    return {
        "total": len(items),
        "stats": {
            "open": open_count,
            "resolved": resolved_count,
            "red": red_count,
            "yellow": yellow_count,
            "sla_breached": sla_breach_count,
        },
        "escalations": items,
    }


@app.post("/api/escalations/{esc_id}/resolve")
def resolve_escalation(
    esc_id: str,
    req: ResolveRequest,
    x_supervisor_key: Optional[str] = Header(None),
):
    if not (x_supervisor_key and hmac.compare_digest(x_supervisor_key, SUPERVISOR_KEY)):
        raise HTTPException(status_code=403, detail="Chiave supervisore non valida")
    store = _load_escalations()
    if esc_id not in store:
        raise HTTPException(status_code=404, detail=f"Escalation {esc_id} non trovata")
    esc = store[esc_id]
    if esc["escalation_status"] == "RESOLVED":
        raise HTTPException(status_code=409, detail="Escalation già risolta")
    resolved_at = datetime.now(timezone.utc).isoformat()
    esc["escalation_status"] = "RESOLVED"
    esc["resolved_at"] = resolved_at
    esc["resolved_by"] = req.resolved_by
    esc["resolution_notes"] = req.resolution_notes
    if esc.get("timestamp") and esc.get("sla_deadline"):
        try:
            created = datetime.fromisoformat(esc["timestamp"].replace("Z", "+00:00"))
            deadline = datetime.fromisoformat(esc["sla_deadline"])
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            esc["resolution_time_hours"] = round((now - created).total_seconds() / 3600, 1)
            esc["resolved_within_sla"] = now <= deadline
        except Exception:
            pass
    store[esc_id] = esc
    _save_escalations(store)
    return {"status": "resolved", "escalation": _enrich_sla(esc)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
