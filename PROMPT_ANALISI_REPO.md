# Prompt analisi repo — Cognitive Logic QEN Framework

Incolla questo testo all'inizio di una nuova sessione Claude Code.

---

## PROMPT

Analizza il repository `CognitiveLogic2026/CognitiveLogic2026.github.io` e fornisci un report completo dello stato attuale. Il progetto è il **QEN Framework** (Quantification of Ethical Naturalness) di Cognitive Logic — piattaforma SaaS B2B per compliance regolatoria EU AI Act + GDPR + Bolkestein 2027 rivolta a operatori HoReCa, balneare e commercio.

### Architettura

**Frontend (GitHub Pages — cognitivelogic.it):**
- Pagine statiche HTML/CSS/JS
- Pagine chiave: `copilot.html`, `discovery.html`, `qen-horeca-auditor.html`, `qen-balneare-auditor.html`, `qen-compliance-auditor.html`, `admin-clienti.html`, `pilots.html`, `qen-live.html`

**Backend (VPS Hetzner — api.cognitivelogic.it, Flask porta 5000):**
- `main.py` — core Flask app, routes `/audit/horeca`, `/audit/balneare`, `/admin/add-client`, `/copilot-analyze`, `/pilots`, `/reconcile/batch`
- `orchestrator.py` — agenti LLM: Claude Sonnet 4.6 + Mistral Large (fallback), endpoints `/agents/*`
- Persistenza: `pilots.json` + `graph.json` su `/app/cognitivelogic/`

**Deploy:**
- `.github/workflows/deploy-vps.yml` → push su `main` trigger deploy SSH su VPS (paths: main.py, orchestrator.py)
- `.github/workflows/deploy-static.yml` → GitHub Pages per HTML statici

### Stato branch

- **main** — produzione stabile
- **claude/mistral-framework-integration-PGxml** — branch attivo con PR #55 aperta (potrebbe essere in attesa di merge)

### Funzionalità implementate

1. **QEN Score** = Vs×0.40 + Va×0.35 + Vt×0.25 (Semantic Legality / Accountability / Territorial Trust)
2. **Auditor settoriali**: HoReCa (8 moduli), Balneare (6 moduli, 7 tipologie), Compliance AI (EU AI Act)
3. **Copilot AI** — analisi EU AI Act + GDPR da testo libero, Claude Sonnet + Mistral Large
4. **Discovery automatica** (`discovery.html`) — Google Places → lista stabilimenti per comune/settore → batch scoring QEN (chunk da 5, Mistral → fallback Claude) → export PDF/CSV lista contatti prioritari → salvataggio in pilots.json + graph.json
5. **Knowledge graph** — nodi `EntitaPilota` in graph.json, visualizzazione in qen-live.html
6. **Bolkestein 2027** — pre-assessment concessioni demaniali con scarcity test e deadline mapping
7. **Admin** — inserimento manuale clienti con API key, lista pilots con QEN history

### Segreti configurati (GitHub Secrets → VPS /etc/cognitivelogic/env)
- `ANTHROPIC_API_KEY` — Claude Sonnet 4.6
- `MISTRAL_API_KEY` — Mistral Large (mistral-large-latest)
- `GOOGLE_PLACES_API_KEY` — Places Text Search API
- `COGNITIVE_API_KEY` — autenticazione admin/discovery
- `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `ICEA_API_KEY`, `INFOCAMERE_API_KEY`, `SUPERVISOR_KEY`

### Cosa analizzare

1. **Stato PR #55** — è stata mergiata? Cosa è in pending?
2. **Stato pilots.json** — quanti nodi mappati, distribuzione settori, range QEN
3. **Endpoint attivi** — verifica che `/agents/score-businesses`, `/agents/places-discovery` rispondano
4. **Prossime priorità** — cosa manca per la prossima release?
5. **Qualità codice** — segnala duplicazioni, endpoint disabilitati (OpenAI), mock non ancora integrati (InfoCamere, CNA)

---

*Generato il 2026-05-30 — sessione Claude Code*
