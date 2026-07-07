# Prompt analisi repo — Cognitive Logic QEN Framework

Incolla questo testo all'inizio di una nuova sessione Claude Code.

---

## PROMPT

Sei Claude Code sul repository `CognitiveLogic2026/CognitiveLogic2026.github.io`.

Il progetto è **Cognitive Logic QEN Framework** — piattaforma SaaS B2B per compliance regolatoria
EU AI Act + GDPR + Bolkestein 2027, rivolta a operatori HoReCa, balneare e commercio italiano.

*Ultimo aggiornamento: 2026-05-31 — sessione P0→P3 fix sicurezza + refactor.*

---

## Architettura

### Frontend (GitHub Pages — cognitivelogic.it)

39 pagine HTML/CSS/JS statiche. Pagine principali:

| Pagina | Scopo |
|--------|-------|
| `copilot.html` | AI copilot EU AI Act + GDPR |
| `discovery.html` | Discovery batch stabilimenti + scoring QEN (richiede COGNITIVE_API_KEY) |
| `qen-horeca-auditor.html` | Auditor verticale HoReCa |
| `qen-balneare-auditor.html` | Auditor verticale Balneare |
| `qen-compliance-auditor.html` | Compliance auditor generico |
| `admin-clienti.html` | Inserimento manuale clienti (COGNITIVE_API_KEY) |
| `qen-live.html` | Knowledge graph interattivo live |
| `escalation.html` | Gestione escalation riconciliazione |
| `operator.html` | Dashboard operatore |

**CSS:** design system proprietario (Cormorant Garamond + DM Mono, dark theme `--gold-soft`)
**JS:** vanilla, chiamate dirette a api.cognitivelogic.it. `app.js` chiama Gemini REST lato client.

### Backend Flask — api.cognitivelogic.it (porta 5000)

File: `main.py` + `orchestrator.py` (registrato via `register_orchestrator(app, limiter)`)

**Endpoint Flask core:**

| Path | Auth | Descrizione |
|------|------|-------------|
| GET `/health` | ❌ | Status check |
| GET `/pilots` | ✅ X-API-Key | Lista pilot entities |
| POST `/audit/horeca` | ❌ | Audit HoReCa 8 moduli → pilots.json |
| POST `/audit/balneare` | ❌ | Audit Balneare 6 moduli |
| POST `/analyze` | ✅ X-API-Key | Crea nodo graph.json |
| POST `/classify-risk` | ✅ X-API-Key | EU AI Act via Claude Sonnet 4.6 (30/min) |
| POST `/copilot-analyze` | ❌ | Risk + dedup pilots (30/min) |
| POST `/gemini/qen-score` | ❌ | QEN via Gemini (fallback Claude Haiku) (30/min) |
| POST `/admin/add-client` | ✅ X-API-Key | Aggiunta manuale client |
| POST `/admin/reconcile-batch` | ✅ X-API-Key | Drift correction formula QEN su pilots.json |

**Endpoint Orchestrator (11 agenti, tutti con rate limit):**

| Path | Rate | LLM primario | Fallback |
|------|------|-------------|---------|
| `/agents/compliance-auditor` | 30/min | Claude Sonnet 4.6 | — |
| `/agents/territorial-mapper` | 30/min | Claude + Google Places | — |
| `/agents/advisory-council` | 30/min | Claude Sonnet 4.6 | — |
| `/agents/intelligence-feed` | — | JSON file (`data/intelligence_feed.json`) | — |
| `/agents/mistral-compliance` | 30/min | Mistral Large | Claude Sonnet 4.6 |
| `/agents/mistral-advisor` | 30/min | Mistral Large | Claude Sonnet 4.6 |
| `/agents/openai-advisor` | — | ❌ 503 stub | — |
| `/agents/bolkestein-assessment` | 30/min | Mistral Large | Claude Sonnet 4.6 |
| `/agents/places-discovery` | — | Google Places API | — |
| `/agents/score-businesses` | 20/min | Mistral / Claude | Claude fallback |
| `/agents/places-batch-qen` | 20/min | Mistral / Claude | Claude fallback |

### Backend FastAPI — porta 8001 (QEN Reconciliation)

File: `qen-reconciliation/main.py`

Logica: `dichiarato vs verificato → discrepanza → aggiustamento penalità → escalation`

```
BASE_SCORE = 75 | ALIGNED: 0 | GREEN: -5 | YELLOW: -15 | RED: -30
```

Endpoint: `GET /health`, `POST /api/ingest`, `POST /api/reconcile`,
`GET /api/escalations`, `POST /api/escalations/{id}/resolve` (X-Supervisor-Key)

Fonti: ICEA (stub), InfoCamere (stub), OpenStreetMap (lambda), NANDO (lambda)

### Nginx Routing (api.cognitivelogic.it)

```
/agents/*, /gemini/*, /admin/*, /audit/*,
/classify-risk, /copilot-analyze, /pilots, /analyze, /validate
  → Flask 5000

/reconcile/* → FastAPI 8001
/           → FastAPI 8001 (default)
```

**Nota:** `/health` non è nella lista Flask — va a FastAPI 8001. La Flask ha il suo `/health`
ma non è raggiungibile dall'esterno via nginx (solo via localhost nel deploy).

### Dati persistenti (VPS /app/cognitivelogic/)

- `pilots.json` — entità con QEN score e history analisi
- `graph.json` — knowledge graph 97 nodi, 182 relazioni
- `escalations.json` — escalation riconciliazione RED/YELLOW

### Moduli non in produzione

- `qen-bolkestein/` — scoring engine Bolkestein, solo locale (nessun systemd service)
- `qen-horeca-auditor/` — FastAPI auditor separato, non esposto via nginx
- `qen_bolkestein_s4.py` — script deploy manuale

---

## Stato fix (2026-05-31)

### Tutti applicati e in main ✅

| PR | Fix | Categoria |
|----|-----|-----------|
| #60 | Health check CI bloccanti, CORS FastAPI, systemd www-data, smoke tests | Security/CI |
| #61 | Auth `GET /pilots` (era pubblico), SUPERVISOR_KEY senza default hardcoded | P0 Security |
| #61 | Rate limiting Flask-Limiter 4.1 (30/20 rpm), CORS allowlist Flask, deps `~=` | P1 Security |
| #62 | `_score_business_list()` condivisa (dedup -80 righe), route `/copilot` rimossa | P2 Refactor |
| #62 | `intelligence_feed` da `data/intelligence_feed.json`, fix deploy `safe.directory` | P3 + Hotfix |
| latest | `/reconcile/batch` spostato a `/admin/reconcile-batch` (era shadowato da nginx) | Bugfix |

### Segreti configurati (GitHub Secrets → /etc/cognitivelogic/env)

| Secret | Stato |
|--------|-------|
| `ANTHROPIC_API_KEY` | ✅ Attivo |
| `MISTRAL_API_KEY` | ✅ Attivo |
| `GOOGLE_PLACES_API_KEY` | ✅ Attivo |
| `GOOGLE_API_KEY` (Gemini) | ✅ Attivo |
| `COGNITIVE_API_KEY` | ✅ Attivo (auth admin + pilots) |
| `SUPERVISOR_KEY` | ✅ Attivo — obbligatorio, RuntimeError senza |
| `ICEA_API_KEY` | ⚠️ Stub — `biologico_certificato` restituisce sempre True |
| `INFOCAMERE_API_KEY` | ⚠️ Stub — scarti/kwh sono mock |
| `OPENAI_API_KEY` | ❌ Disabilitato (pagamento pending) |

---

## Problemi aperti residui

1. **Rate limiter multi-worker** — Gunicorn `--workers 2` + in-memory: limite effettivo 2× per IP.
   Soluzione: Redis backend o ridurre a 1 worker. Documentato in `VALIDATION_STATUS.md`.

2. **Gemini lato client in `app.js`** — chiamata diretta a `generativelanguage.googleapis.com`
   con chiave in `js/config.js` (in `.gitignore`). Pattern rischioso, chiave esposta nel browser.
   Soluzione: proxiare via `/gemini/qen-score` già esistente nel backend.

3. **`/health` Flask non raggiungibile** — nginx non lo instrada. Aggiungere al regex:
   `location ~ ^/(classify-risk|...|health)$` in `nginx/api.cognitivelogic.it.conf`.

4. **Zero test per orchestrator** — nessun test per i 11 agenti. Aggiungere mock LLM almeno
   per `compliance-auditor` e `bolkestein-assessment`.

5. **ICEA/InfoCamere stub** — dati riconciliazione non verificati da fonte ufficiale.
   Da attivare con chiavi reali quando disponibili.

---

## Workflow CI/CD attivi

| Workflow | Trigger | Job |
|----------|---------|-----|
| `deploy-vps.yml` | push main (main.py, orchestrator.py, nginx/, data/intelligence_feed.json) | SSH deploy → VPS |
| `deploy-static.yml` | push main (HTML, css/, js/) | SSH sync static |
| `test.yml` | push main, PR→main | pytest tests/ -v |
| `security-scan.yml` | tutti i branch, PR→main | grep hardcoded secrets |
| `sync-fuorimenu.yml` | schedule settimanale | sync RSS Substack |

---

## QEN Formula

```
QEN = (Vs × 0.40) + (Va × 0.35) + (Vt × 0.25)

Vs = Valore Sociale    (HR, compliance, equità)
Va = Valore Ambientale (energia, rifiuti, filiera)
Vt = Valore Territoriale (locale, stakeholder, governance)

Range: 0-100 | Soglie: <60 critico, 60-70 medio, 70-85 buono, >85 eccellente
```

---

## Roadmap

- **Q2 2026:** Freemium badge QEN pubblico, 10 pilot certificati, P.IVA attiva
- **Q3 2026:** Partnership CNA Bologna, 5 clienti pro, ETL open.er.it
- **Q4 2026:** White label Confartigianato, Bologna 100 Botteghe, Dashboard B2G
- **Q1 2027:** ETL TelemacoPay, Neo4j produzione, 2000+ nodi, ICEA/InfoCamere reali

---

*Generato: 2026-05-31 — sessione P0→P3 + refactor completo*
