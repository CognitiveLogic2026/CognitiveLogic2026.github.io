# Prompt analisi repo — Cognitive Logic QEN Framework

Incolla questo testo all'inizio di una nuova sessione Claude Code.

---

## PROMPT

Sei Claude Code sul repository `CognitiveLogic2026/CognitiveLogic2026.github.io`.

Il progetto è **Cognitive Logic QEN Framework** — piattaforma SaaS B2B per compliance regolatoria
EU AI Act + GDPR + Bolkestein 2027, rivolta a operatori HoReCa, balneare e commercio italiano.

*Ultimo aggiornamento: 2026-05-31 — sessione di validazione e fix sicurezza.*

---

## Architettura

### Frontend (GitHub Pages — cognitivelogic.it)

39 pagine HTML/CSS/JS statiche. Pagine principali:

| Pagina | Scopo |
|--------|-------|
| `copilot.html` | AI copilot EU AI Act + GDPR |
| `discovery.html` | Discovery batch stabilimenti + scoring QEN |
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

File: `main.py` (503 linee) + `orchestrator.py` (741 linee, registrato via `register_orchestrator(app)`)

**Endpoint Flask core:**

| Path | Auth | Descrizione |
|------|------|-------------|
| GET `/health` | ❌ | Status check |
| GET `/pilots` | ❌ | Lista pilot entities (84 attivi) |
| POST `/audit/horeca` | ❌ | Audit HoReCa 8 moduli → pilots.json |
| POST `/audit/balneare` | ❌ | Audit Balneare 6 moduli |
| POST `/analyze` | ✅ X-API-Key | Crea nodo graph.json |
| POST `/classify-risk` | ✅ X-API-Key | EU AI Act via Claude Sonnet 4.6 |
| POST `/copilot-analyze` | ❌ | Risk + dedup pilots |
| POST `/gemini/qen-score` | ❌ | QEN via Gemini (fallback Claude Haiku) |
| POST `/admin/add-client` | ✅ X-API-Key | Aggiunta manuale client |
| POST `/reconcile/batch` | ✅ X-API-Key | Batch riconciliazione formula QEN |

**Endpoint Orchestrator (11 agenti):**

| Path | LLM primario | Fallback |
|------|-------------|---------|
| `/agents/compliance-auditor` | Claude Sonnet 4.6 | — |
| `/agents/territorial-mapper` | Claude + Google Places | — |
| `/agents/advisory-council` | Claude Sonnet 4.6 | — |
| `/agents/intelligence-feed` | JSON statico | — |
| `/agents/mistral-compliance` | Mistral Large | Claude Sonnet 4.6 |
| `/agents/mistral-advisor` | Mistral Large | Claude Sonnet 4.6 |
| `/agents/openai-advisor` | ❌ 503 stub | — |
| `/agents/bolkestein-assessment` | Mistral Large | Claude Sonnet 4.6 |
| `/agents/places-discovery` | Google Places API | — |
| `/agents/score-businesses` | Mistral / Claude | Claude fallback |
| `/agents/places-batch-qen` | Mistral / Claude | Claude fallback |

### Backend FastAPI — porta 8001 (QEN Reconciliation)

File: `qen-reconciliation/main.py` (348 linee)

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
/classify-risk, /copilot-analyze, /copilot, /pilots, /analyze, /validate
  → Flask 5000

/reconcile/* → FastAPI 8001
/           → FastAPI 8001 (default)
```

**Nota:** `/health` NON è nella lista Flask — va a FastAPI 8001. La Flask è healthy ma il suo
`/health` non è raggiungibile dall'esterno via nginx.

### Dati persistenti (VPS /app/cognitivelogic/)

- `pilots.json` — 84 entità con QEN score, history analisi
- `graph.json` — knowledge graph 67 nodi, 105 relazioni
- `escalations.json` — escalation riconciliazione RED/YELLOW

### Moduli non in produzione

- `qen-bolkestein/` — Neo4j + async batch processor, solo locale (nessun systemd service)
- `qen-horeca-auditor/` — FastAPI auditor separato, non esposto via nginx
- `qen_bolkestein_s4.py` — script deploy manuale

---

## Stato attuale (2026-05-31)

### Fix applicati nella sessione precedente (PR #60, mergiata e deployata ✅)

| Fix | Commit | Stato |
|-----|--------|-------|
| Health check bloccanti nel deploy (exit 1) | `36de612` | ✅ In produzione |
| CORS FastAPI ristretto a cognitivelogic.it | `a14f974` | ✅ In produzione |
| Security scan esteso a file .html | `5f3c5e1` | ✅ In produzione |
| openai_advisor() → 503 standardizzato | `503b7ad` | ✅ In produzione |
| systemd User=www-data (non root) | `97c5e64` | ✅ In produzione |
| Smoke tests pytest + workflow test.yml | `b5e5d3f` | ✅ In produzione |
| VALIDATION_STATUS.md | `d331039` | ✅ In produzione |

### Segreti configurati (GitHub Secrets → /etc/cognitivelogic/env)

| Secret | Stato |
|--------|-------|
| `ANTHROPIC_API_KEY` | ✅ Attivo |
| `MISTRAL_API_KEY` | ✅ Attivo |
| `GOOGLE_PLACES_API_KEY` | ✅ Attivo |
| `GOOGLE_API_KEY` (Gemini) | ✅ Attivo |
| `COGNITIVE_API_KEY` | ✅ Attivo (auth admin) |
| `SUPERVISOR_KEY` | ✅ Attivo (resolver escalation) |
| `ICEA_API_KEY` | ⚠️ Stub — biologico_certificato è mock |
| `INFOCAMERE_API_KEY` | ⚠️ Stub — scarti/kwh sono mock |
| `OPENAI_API_KEY` | ❌ Disabilitato (pagamento pending) |

---

## Problemi aperti da risolvere

### Sicurezza — Alta priorità

1. **No rate limiting** su nessun endpoint. `/gemini/qen-score`, `/audit/horeca`, `/audit/balneare`
   sono pubblici e senza limiti. Soluzione: Flask-Limiter o nginx `limit_req_zone`.

2. **Gemini API key lato client** — `js/app.js` chiama direttamente
   `generativelanguage.googleapis.com` con chiave non censita in `.gitignore`. La chiave è in
   `js/config.js` che è in `.gitignore`, ma il pattern è rischioso. Soluzione: proxiare la
   chiamata Gemini via backend Flask.

3. **Flask CORS fallback wildcard** — riga 24-26 `main.py`:
   ```python
   if 'cognitivelogic.it' in origin or not origin:
       response.headers['Access-Control-Allow-Origin'] = origin or '*'
   ```
   Se `origin=""` → risponde con `*`. Rimuovere il fallback `or '*'`.

4. **X-Supervisor-Key mismatch** — FastAPI FastAPI usa `x_supervisor_key` (underscore),
   ma HTTP invia `X-Supervisor-Key` (hyphen). Da verificare in produzione con
   `POST /api/escalations/{id}/resolve`.

### Dipendenze

5. **Requirements non pinnati** — tutti i file usano `>=` (range). Rischioso per aggiornamenti
   non controllati. Pinnare con `pip freeze` o usare `pip-tools`.

6. **httpx non in requirements** — TestClient FastAPI dipende da httpx, installato solo in
   `test.yml` come extra. Aggiungere a `qen-reconciliation/requirements.txt`.

### Backend

7. **Flask `/health` non esposta via nginx** — il regex nginx non include `/health` tra le route
   Flask. Il deploy health check funziona via localhost ma non dall'esterno.
   Aggiungere `/health` al regex in `nginx/api.cognitivelogic.it.conf`.

8. **intelligence-feed statico** — `/agents/intelligence-feed` ritorna JSON hardcoded con
   date fisse (deadline CSRD 2026-06-30 è già passata). Aggiornare o rendere dinamico.

9. **Duplicazione Gemini calls** — `main.py` e `orchestrator.py` hanno entrambi codice per
   chiamare Gemini via REST. Centralizzare in un helper.

### Test

10. **Zero test per orchestrator** — nessun test per i 10 agenti attivi. Aggiungere test
    parametrizzati con mock LLM per almeno compliance-auditor e bolkestein-assessment.

---

## Workflow CI/CD attivi

| Workflow | Trigger | Job |
|----------|---------|-----|
| `deploy-vps.yml` | push main (main.py, orchestrator.py, nginx/) | SSH deploy → VPS |
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

## Roadmap (da pianificare)

- **Q2 2026:** Freemium badge QEN pubblico, 10 pilot certificati
- **Q3 2026:** Partnership CNA Bologna, 5 clienti pro
- **Q4 2026:** White label per Confartigianato, 100 audit
- **Q1 2027:** ETL 2000+ nodi, Neo4j in produzione, integrazione ICEA/InfoCamere reali

---

*Generato: 2026-05-31 — sessione fix validazione + analisi completa repo*
