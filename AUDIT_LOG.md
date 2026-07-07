# Audit Log — CognitiveLogic QEN Platform

Registro delle verifiche di coerenza numerica e testuale condotte sul repository.
Non sostituisce `VALIDATION_STATUS.md` (stato tecnico di dipendenze/servizi): qui
si registrano gli esiti di audit puntuali su contenuti, dati e riferimenti.

---

## Audit — Riferimenti a cognitivelogic.it (2026-07-07)

Verificato 2026-07-07: i riferimenti a `cognitivelogic.it` nei 59 file sottostanti sono
corretti e non richiedono marcatura DNS — si autorisolvono automaticamente al ripristino
del dominio. A differenza di `llms.txt` e `robots.txt` (bridge temporaneo verso il mirror
GitHub Pages, cfr. PR #138, marcati con "ACTION ON DNS RESTORE"), questi 59 file citano
già correttamente il dominio proprio `cognitivelogic.it` e non un workaround. Nessuna
azione necessaria.

File verificati (59):
`.well-known/did.json`, `.well-known/governance-layer-manifest.json`,
`DOSSIER_SIAE_QEN_COMPLETO.html`, `ELENCO_PAGINE.md`, `PROMPT_ANALISI_REPO.md`,
`QEN_DOSSIER_NOTARILE.html`, `QEN_DOSSIER_NOTARILE.md`, `QEN_RECONCILIAZIONE_PROMPT.md`,
`README.md`, `SIAE_CD_ISTRUZIONI_COPISTERIA.html`, `VALIDATION_STATUS.md`,
`academia/index.html`, `admin-clienti.html`, `ai.html`, `ai_en.html`, `alert-engine.html`,
`cna/index.html`, `competitive-analysis.html`, `cookie.html`, `copilot.html`,
`data/evide-registry.json`, `data/qen_graph_v4.json`, `demo.html`, `discovery.html`,
`eci-assessment.html`, `ecosystem.html`, `ecosystem_en.html`, `escalation.html`,
`evide.html`, `framework.html`, `framework_en.html`, `guida-operatore.html`,
`identity.html`, `identity_en.html`, `index_en.html`, `legal.html`, `llm-index.html`,
`logo-preview.html`, `mascot.html`, `onboarding.html`, `opensearchdescription.xml`,
`operator-portal.html`, `operator.html`, `operatore.html`, `operatori.html`,
`pilots.html`, `presentazione.html`, `privacy.html`, `qen-balneare-auditor.html`,
`qen-compliance-auditor.html`, `qen-horeca-auditor.html`, `qen-live.html`,
`qen-prompt-generator.html`, `qen-widget.html`, `qen.html`, `research.html`,
`ristorazione.html`, `robertomalini/did.json`, `services.html`.

**Eccezione permanente**: `DOSSIER_SIAE_QEN_COMPLETO.html` è già depositato via SIAE
PRSW Mod. 349 (3 luglio 2026). Non va mai modificato — nessuna marcatura, nessun edit —
senza conferma esplicita separata dell'autore, indipendentemente da qualunque audit
successivo.
