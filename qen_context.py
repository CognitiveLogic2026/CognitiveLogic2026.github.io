"""
qen_context.py — Contesto condiviso del framework QEN (Quantification of Ethical Naturalness)

NOTA STATO INFRASTRUTTURA (aggiornato 2026-07-12, diagnosi VPS):
- qen-framework.service, qen-api.service, qen-copilot.service (porta 8000): DISATTIVATI
  (systemctl disable --now, 12/7/2026). Caricavano app.py, uno stub FastAPI senza logica
  reale. Vedi API_ENDPOINTS_PIANIFICATI_NON_ATTIVI sotto.
- gemini_backend.py (PM2, porta 5001): in esecuzione ma SCOLLEGATO da main.py.
- /gemini/qen-score e /gemini/compliance-audit sono rotte DENTRO main.py su Flask :5000.
- Backend reali: Flask :5000 (cognitivelogic-flask.service) e FastAPI :8001 (cognitivelogic.service).
"""

QEN_FRAMEWORK_VERSION = "Diamante 26.0"
QEN_API_VERSION = "3.2"
QEN_GRAPH_VERSION = "6.0"
QEN_RECONCILIATION_VERSION = "2.0.0"
AUTHOR = "Roberto Bob Malini"
AUTHOR_CF = "MLNRRT62H06A944U"
AUTHOR_DID = "did:web:cognitivelogic.it:robertomalini"
ORGANIZATION = "Cognitive Logic"
DOMAIN = "cognitivelogic.it"
API_DOMAIN = "api.cognitivelogic.it"
LICENSE = "CC BY-SA 4.0"

QEN_WEIGHT_VS = 0.40
QEN_WEIGHT_VA = 0.35
QEN_WEIGHT_VT = 0.25
QEN_BASE_SCORE = 75
QEN_SCORE_MIN = 0
QEN_SCORE_MAX = 100
QEN_SCALE_THRESHOLD = 10
QEN_SCALE_FACTOR = 10

def qen_score(vs, va, vt):
    if max(vs, va, vt) <= QEN_SCALE_THRESHOLD:
        vs, va, vt = vs * QEN_SCALE_FACTOR, va * QEN_SCALE_FACTOR, vt * QEN_SCALE_FACTOR
    return round(vs * QEN_WEIGHT_VS + va * QEN_WEIGHT_VA + vt * QEN_WEIGHT_VT, 2)

def qen_score_copilot(vs, va, vt):
    if max(vs, va, vt) <= QEN_SCALE_THRESHOLD:
        vs, va, vt = vs * QEN_SCALE_FACTOR, va * QEN_SCALE_FACTOR, vt * QEN_SCALE_FACTOR
    return round((vs + va + vt) / 3, 2)

QEN_BADGE_LEVELS = [
    {"label": "QEN Diamante", "min": 90, "max": 100, "color": "#1a5276"},
    {"label": "QEN Oro", "min": 80, "max": 89, "color": "#d4ac0d"},
    {"label": "QEN Argento", "min": 70, "max": 79, "color": "#797d7f"},
    {"label": "QEN Bronzo", "min": 60, "max": 69, "color": "#935116"},
    {"label": "QEN In Sviluppo", "min": 0, "max": 59, "color": "#7f8c8d"},
]

def qen_badge(score):
    for b in QEN_BADGE_LEVELS:
        if b["min"] <= score <= b["max"]:
            return b["label"]
    return "QEN In Sviluppo"

RECONCILIATION_THRESHOLDS = {"ALIGNED": 0.00, "GREEN": 0.15, "YELLOW": 0.30}
RECONCILIATION_ADJUSTMENTS = {"ALIGNED": 0, "GREEN": -5, "YELLOW": -15, "RED": -30}

RECONCILABLE_PARAMETERS = {
    "distanza_media_fornitori_km": {"source": "OpenStreetMap", "reliability": 0.75, "type": "numeric", "fallback": 115.0},
    "biologico_certificato": {"source": "ICEA", "reliability": 0.90, "type": "boolean", "fallback": True, "env_key": "ICEA_API_KEY"},
    "percentuale_scarti": {"source": "InfoCamere", "reliability": 0.75, "type": "numeric", "fallback": 12.0, "env_key": "INFOCAMERE_API_KEY"},
    "consumo_kwh_anno": {"source": "InfoCamere", "reliability": 0.75, "type": "numeric", "fallback": 45000, "env_key": "INFOCAMERE_API_KEY"},
    "eu_ai_compliant": {"source": "NANDO", "reliability": 0.92, "type": "boolean", "fallback": True},
}

CLAUDE_MODEL = "claude-sonnet-4-6"
GEMINI_MODEL_CASCADE = ["gemini-2.0-flash-lite", "gemini-2.5-flash", "gemini-2.0-flash"]
MISTRAL_MODEL = "mistral-large-latest"
LLM_MAX_TOKENS_AUDIT = 1500
LLM_MAX_TOKENS_SCORE = 900
LLM_MAX_TOKENS_BATCH = 1200
LLM_TEMPERATURE_DEFAULT = 0.3
RATE_LIMIT_LLM_SINGLE = 30
RATE_LIMIT_LLM_BATCH = 20

SYSTEM_COMPLIANCE_AUDITOR = (
    "Sei il Compliance Auditor del framework QEN. Analizza applicando EU AI Act, "
    "GDPR (Art.22, Art.35), CSRD/Green Claims. QEN Score: vs*0.40 + va*0.35 + vt*0.25 (0-100). "
    "Rispondi SOLO con JSON valido: "
    '{"qen_score": 0.0, "vs": 0.0, "va": 0.0, "vt": 0.0, '
    '"eu_ai_act": {"allegato": "", "livello_rischio": "", "motivazione": ""}, '
    '"gdpr": {"risk": "", "dpia_required": false, "articoli": []}, '
    '"gaps": [], "remediation": [], "summary": ""}'
)

SYSTEM_TERRITORIAL_MAPPER = (
    "Sei il Territorial Mapper del framework QEN. Mappa stakeholder locali, filiera corta, "
    "fornitori entro 100km, impatto occupazionale, DE.CO. "
    "Rispondi SOLO con JSON valido: "
    '{"vt_score": 0.0, "stakeholders": [], "supply_chain": '
    '{"local_pct": 0.0, "avg_distance_km": 0.0, "certifications": []}, '
    '"territorial_impact": "", "recommendations": [], "summary": ""}'
)

SYSTEM_ADVISORY_COUNCIL = (
    "Sei l'Advisory Council del framework QEN, esperto normativo EU. Consulenza su EU AI Act, "
    "GDPR, CSRD, Bolkestein 2027. "
    "Rispondi SOLO con JSON valido: "
    '{"priority_actions": [], "compliance_timeline": [], '
    '"regulatory_refs": [], "cost_estimate": "", "summary": ""}'
)

SYSTEM_DISCOVERY_QEN = (
    "Sei il Discovery Pre-Assessor del framework QEN. Stima un QEN pre-assessment da dati "
    "pubblici minimi per HoReCa / balneare / commercio. Formula: qen_score = Vs*0.35 + Va*0.35 + Vt*0.30. "
    "Rispondi SOLO con JSON valido: "
    '{"qen_score": 0.0, "vs": 0.0, "va": 0.0, "vt": 0.0, '
    '"confidence": "LOW|MEDIUM", "risk_flags": [], "bolkestein_applicable": false, '
    '"summary": "", "note": "Pre-assessment da dati pubblici"}'
)

SYSTEM_BOLKESTEIN_ASSESSOR = (
    "Sei esperto della Direttiva Servizi EU 2006/123/CE (Bolkestein), concessioni con scadenza "
    "2027. Applica test di scarsita', RIGI, giurisprudenza CGUE (C-458/14, C-20/21). "
    "Rispondi SOLO con JSON valido: "
    '{"risk_level": "ALTO|MEDIO|BASSO", "concession_type": "", '
    '"scarcity_test": {"result": "SCARSA|NON_SCARSA|INCERTA", "justification": ""}, '
    '"imperative_reasons": [], "compliance_actions": [], '
    '"critical_deadlines": [{"date": "", "action": ""}], '
    '"qen_preassessment": {"score": 0.0, "vs": 0.0, "va": 0.0, "vt": 0.0, "note": ""}, '
    '"regulatory_refs": [], "summary": ""}'
)

SYSTEM_INTELLIGENCE_FEED = (
    "Sei l'Intelligence Feed Analyst del framework QEN per operatori HoReCa. "
    "Rispondi SOLO con JSON valido: "
    '{"alerts": [], "opportunities": [], "regulatory_updates": [], '
    '"market_signals": [], "summary": ""}'
)

SYSTEM_QEN_RECONCILIATION = (
    "Sei il motore di riconciliazione QEN. Confronta parametri autodichiarati con valori "
    "verificati, calcola scostamento, assegna stato ALIGNED/GREEN/YELLOW/RED, applica "
    "aggiustamento, apri escalation per RED/YELLOW. Restituisci solo JSON, nessun testo."
)

PLACES_QUERIES_BY_SECTOR = {
    "balneare": ["stabilimento balneare {comune}", "lido balneare {comune}", "beach club {comune}"],
    "horeca": ["ristorante trattoria {comune}", "pizzeria {comune}", "osteria {comune}"],
    "alberghiero": ["hotel {comune}", "albergo bed and breakfast {comune}"],
    "commercio": ["negozio mercato {comune}", "bottega artigiana {comune}"],
}

PLACES_SUPPLY_CHAIN_QUERIES = ["produttori agricoli locali {location}", "cooperativa alimentare {location}"]

MARKET_VERTICALS = {
    "FOOD": {
        "label": "Ristorazione e Food",
        "algoritmi": ["COLT_IN_FRAGRANZA", "VEGANOO"],
        "kpi_primari": ["biologico_certificato", "percentuale_scarti", "distanza_media_fornitori_km"],
        "settori_istat": ["56.10", "56.21", "56.29", "56.30"],
    },
    "BALNEARE": {
        "label": "Stabilimenti Balneari",
        "algoritmi": ["ECO_LOCAL"],
        "kpi_primari": ["consumo_kwh_anno", "percentuale_scarti", "eu_ai_compliant"],
        "scadenza_bolkestein": "2027-12-31",
        "strutture_riviera": 1850,
    },
    "PMI": {
        "label": "PMI Artigianato e Commercio",
        "algoritmi": ["TRAD_RAD", "BOLOGNA_100_BOTTEGHE"],
        "kpi_primari": ["distanza_media_fornitori_km", "biologico_certificato"],
        "settori_istat": ["47", "95", "96"],
    },
}

REGULATORY_FRAMEWORK = {
    "EU_AI_ACT": {"ref": "Reg. UE 2024/1689", "applicazione": "Sistemi AI ad alto rischio", "stato": "CONFORME", "allegati": ["I", "II", "III"]},
    "GDPR": {"ref": "Reg. UE 2016/679", "applicazione": "Art.22, Art.35 DPIA", "stato": "CONFORME"},
    "BOLKESTEIN": {"ref": "Dir. 2006/123/CE - scadenza 2027", "applicazione": "Modulo qen-bolkestein/ per concessioni balneari, mercati, taxi", "stato": "IN_SVILUPPO"},
    "CSRD": {"ref": "Dir. 2022/2464/UE", "applicazione": "Metriche VA per reporting sostenibilita'", "stato": "IN_SVILUPPO"},
    "CODICE_CONSUMO": {"ref": "D.Lgs. 206/2005", "applicazione": "Trasparenza scoring consumatori", "stato": "CONFORME"},
}

API_ENDPOINTS_ATTIVI = {
    "GET /health": "Stato servizio e versione",
    "POST /copilot-analyze": "Scoring QEN + analisi LLM Gemini",
    "POST /audit/horeca": "Salvataggio audit HoReCa completato",
    "POST /audit/balneare": "Salvataggio audit balneare completato",
    "POST /classify-risk": "Classificazione rischio",
    "GET/POST /admin/*": "Amministrazione (autenticato)",
    "GET/POST /evide/*": "Modulo Evide, audit trail con hash/prev_hash",
    "POST /gemini/qen-score": "QEN scoring via Gemini, dentro main.py :5000",
    "POST /gemini/compliance-audit": "Audit compliance via Gemini, dentro main.py :5000",
    "POST /agents/compliance-auditor": "Audit compliance via Claude, live su :5000 (orchestrator.py)",
    "POST /agents/territorial-mapper": "Mappatura territoriale via Claude + Google Places",
    "POST /agents/advisory-council": "Consulenza normativa via Claude",
    "GET /agents/intelligence-feed": "Feed da data/intelligence_feed.json",
    "POST /agents/mistral-compliance": "Audit compliance via Mistral, fallback Claude",
    "POST /agents/mistral-advisor": "Consulenza via Mistral, fallback Claude",
    "POST /agents/bolkestein-assessment": "Pre-assessment Bolkestein via Mistral/Claude",
    "POST /agents/places-discovery": "Discovery aziende via Google Places",
    "POST /agents/score-businesses": "Scoring QEN batch su lista aziende",
    "POST /agents/places-batch-qen": "Discovery + scoring in una chiamata",
    "GET /health (FastAPI :8001)": "Stato servizio riconciliazione",
    "POST /api/ingest": "Acquisizione dati dichiarati",
    "POST /api/reconcile": "Riconciliazione completa + aggiornamento score",
    "GET /api/escalations": "Lista escalation",
}

API_ENDPOINTS_PIANIFICATI_NON_ATTIVI = {
    "POST /agents/openai-advisor": "Presente in orchestrator.py ma disabilitata a mano, sempre 503",
}
CORS_ORIGINS = frozenset({"https://cognitivelogic.it", "https://www.cognitivelogic.it", "https://api.cognitivelogic.it"})
TRUSTED_HOSTS = frozenset({"cognitivelogic.it", "www.cognitivelogic.it", "api.cognitivelogic.it"})
SUPERVISOR_HEADER = "X-Supervisor-Key"

PATHS = {
    "graph": "/app/cognitivelogic/graph.json",
    "pilots": "/app/cognitivelogic/pilots.json",
    "escalations": "/app/cognitivelogic/escalations.json",
}
