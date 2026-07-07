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

---

## Item aperti — VPS e riconciliazione Neo4j (2026-07-07)

### 1. pm2-logrotate da installare sulla VPS

La VPS ha già riempito il disco una volta a causa di log non ruotati di processi
gestiti via pm2. Nessun deploy automatizzato di questo repo usa pm2 (il backend
QEN gira su systemd + gunicorn/uvicorn, cfr. `deploy-vps.yml`), quindi l'installazione
va fatta manualmente via SSH sulla VPS, fuori dalla pipeline CI/CD:

```
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7
pm2 set pm2-logrotate:compress true
```

Azione non eseguibile da questa sessione (nessun accesso SSH alla VPS). Da fare
manualmente o da una sessione con accesso diretto.

### 2. Blocco 3 — nota di deprecazione Neo4j nel dossier SIAE

Nota di deprecazione Neo4j nel dossier SIAE: **mai applicata, in attesa di conferma**
dell'autore (vedi eccezione permanente sopra — il dossier non si tocca senza
autorizzazione esplicita).

Complicazione emersa: su VPS esiste un'istanza Neo4j reale (`/root/neo4j`,
`/var/lib/neo4j`, rispettivamente 520M e 626M) — dato che contraddice la narrativa
"mai in produzione" usata finora in `PROMPT_ANALISI_REPO.md` (roadmap: "Q1 2027
Neo4j produzione") e implicitamente nel dossier stesso. Prima di applicare qualunque
nota di deprecazione va chiarito con l'autore se quell'istanza è: (a) un residuo di
test/sviluppo mai ripulito, (b) un uso reale non ancora documentato, oppure (c) da
rimuovere. Nessuna modifica al dossier finché questo punto non è confermato.

**Verifica eseguita (2026-07-07)** — evidenza raccolta direttamente su VPS:

- `systemctl status neo4j`: `disabled` / `inactive (dead)` — non parte al boot, non in
  esecuzione.
- Log (`debug.log`): istanza creata `2026-05-12`, avviata/fermata solo a intermittenza
  tra 28 maggio e 2 giugno 2026, mai più toccata da allora.
- Store on-disk: **912 KiB totali** (`neostore.*`), `last committed transaction id: 17`
  — schema di default, nessun dato reale (nessun grafo, nessun nodo applicativo).
  I 520M+626M osservati su `/root/neo4j` e `/var/lib/neo4j` sono quasi certamente
  binari/dipendenze dell'installazione, non dati.
- Un solo tentativo di connessione bolt registrato, fallito per autenticazione.

**Esito**: residuo di test/esplorazione mai ripulito (opzione a), non uso reale in
produzione. La narrativa "mai in produzione" in `PROMPT_ANALISI_REPO.md` e nel
dossier resta corretta — non serve alcuna correzione di sostanza. Resta comunque
valido il vincolo di non modificare `DOSSIER_SIAE_QEN_COMPLETO.html` senza conferma
esplicita separata dell'autore, indipendentemente da questo esito.
