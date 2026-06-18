# Dossier di Autenticazione Notarile — QEN Framework
## QEN — Quantificazione Etica Naturale | Cognitive Logic | Bologna, Italia
**Data preparazione:** 27 maggio 2026 — **Aggiornato:** 18 giugno 2026  
**Oggetto:** Certificazione di data certa per framework semantico QEN — Quantificazione Etica Naturale  
**Sigla ufficiale:** QEN = Quantificazione Etica Naturale (IT) / Quantifying Ethical Network (EN)  
**Data più antica documentata:** 11 novembre 2025 (registrazione dominio cognitivelogic.it)

---

## 1. INTESTAZIONE FORMALE

```
Richiedente: Roberto Malini
Codice Fiscale: MLNRRT62H06A944U
Residenza: Via Della Costituzione 11 — 40033 Casalecchio di Reno (BO)
Finalità: Certificazione di data certa e autenticità di opera intellettuale originale
Studio notarile consigliato: [TBD — preferibilmente Bologna / Casalecchio di Reno]
```

> **Nota identificativa:** Il richiedente è conosciuto professionalmente anche come "Roberto Bob Malini"
> ("Bob" è soprannome d'uso). Ai fini del presente atto notarile si utilizza esclusivamente il nome
> anagrafico **Roberto Malini** (CF: MLNRRT62H06A944U), al fine di distinguersi univocamente
> dall'omonimo scrittore e autore Roberto Malini attivo in ambito letterario.

---

## 2. DESCRIZIONE DELL'OPERA INTELLETTUALE

### 2.1 Titolo e Genere
**QEN Framework — Quantificazione Etica Naturale — Sistema di Scoring Etico per Operatori HoReCa**
- Genere: Framework semantico + Sistema di scoring + Infrastruttura dati
- Natura: Software, documentazione, metodologia proprietaria
- Stato: MVP completato, 4 agenti live in produzione

### 2.2 Ambito di Applicazione
- **Settore:** Food ethics, sustainability governance, AI-driven compliance
- **Target:** HoReCa (ristorazione, alberghiero, balneare)
- **Geografico:** Emilia-Romagna (pilota CNA Bologna)

### 2.3 Cronologia Documentata — Prove di Anteriorità

| Data | Evento | Fonte / Prova |
|------|--------|---------------|
| **11 novembre 2025** | Registrazione dominio cognitivelogic.it | WHOIS — "Created November 11, 2025" (S5b) |
| **20 gennaio 2026** | Prima stesura manuale operativo motore QEN | `QEN_ALGORITMO.pdf` — data intestazione documento |
| **25 febbraio 2026** | Prima indicizzazione pubblica sito | Microsoft Bing Webmaster Tools — prima submission sitemap (S4) |
| **8 giugno 2026** | 493 commit GitHub certificati | Screenshot repo CognitiveLogic2026 (S1) |
| Early 2026 | Inizio sviluppo QEN — Quantificazione Etica Naturale | — |
| **25 maggio 2026** | Completamento MVP | Deploy log Hetzner |
| **26–27 maggio 2026** | Deployment in produzione | Console Hetzner VPS |

> **Nota legale:** La data più antica documentata da terze parti indipendenti è **11 novembre 2025** (registrazione dominio, certificata da WHOIS). Il primo documento interno datato del framework è **20 gennaio 2026** (`QEN_ALGORITMO.pdf`). La prima prova di pubblicazione pubblica verificabile è **25 febbraio 2026** (Bing Webmaster Tools — Microsoft).
>
> **Nota sulla sigla:** `QEN_ALGORITMO.pdf` riporta la variante "Quantificazione dell'Etica Naturale" (con articolo). Ai fini del presente deposito la sigla ufficiale è **QEN — Quantificazione Etica Naturale** (senza articolo), come stabilito in tutti i documenti successivi.

---

## 3. COMPONENTI TECNICHE (da allegare in copia autentica)

### 3.1 Codice Sorgente
**File principale:** `orchestrator.py` (FastAPI backend)
- **Ubicazione:** `/root/cognitive-logic-api/orchestrator.py` (Hetzner VPS CAX21 `cognitive-node-01`)
- **Lingua:** Python 3.9+
- **Linee di codice:** ~350–400 linee
- **Endpoints principali:**
  - `/agents/compliance-auditor` — Auditing normativo EU AI Act / GDPR
  - `/agents/territorial-mapper` — Mappatura geografica (OpenStreetMap, InfoCamere)
  - `/agents/advisory-council` — Consulenza strategica multi-stakeholder
  - `/agents/intelligence-feed` — Monitoraggio real-time compliance

**Moduli correlati:**
- `qen_context.py` — Iniezione di contesto QEN nel system prompt Claude Sonnet
- `graph_expanded.json` — Knowledge graph semantica (130 nodi, 209 edge)

### 3.2 Documentazione Metodologica
**File:** `QEN_FRAMEWORK_SPECIFICATION.md`
- Formula di scoring: `Vs×0.40 + Va×0.35 + Vt×0.25`
  - Vs = Valore Sociale
  - Va = Valore Ambientale
  - Vt = Valore Territoriale
- Scala: 0–100 punti
- Threshold di certificazione: ≥75 punti

**Casi pilota documentati:**
1. Veganoo (Bologna) — Score: 79.0
2. Colt Fragranza (Bologna) — Score: 81.2
3. Bologna100Botteghe (progetto) — Score: 79.5
4. Benchmark CNA Bologna: 77.75

### 3.3 Architettura Infrastrutturale
**File:** `INFRASTRUCTURE_SPEC.md`
- **Server:** Hetzner CAX21 ARM64 (`cognitive-node-01`, IP 178.104.190.107)
- **Stack:** FastAPI + Claude Sonnet 4.6 API + Neo4j (dismesso) → JSON graph
- **CI/CD:** GitHub Actions (repo `CognitiveLogic2026/CognitiveLogic2026.github.io`)
- **Reconciliation engine:** `/reconcile` endpoint (architettura, non ancora implementato)

### 3.4 Protocollo di Riconciliazione Multi-Source
**File:** `RECONCILIATION_PROTOCOL.md`
- **Fonti esterne:** 9 database
  - Certificazioni: ICEA, CCPB
  - Geografiche: OpenStreetMap, InfoCamere
  - EU Compliance: NANDO (AI Act), RASFF
- **Tolleranza discrepanze:** GREEN (0–15%), YELLOW (15–30%), RED (>30%)
- **Autorità di arbitrato:** Source affidability score (non operatore, non sistema manuale)

---

## 4. ALLEGATI FISICI (da stampare e consegnare al notaio)

### 4.1 Codice Sorgente Stampato
- [ ] `orchestrator.py` (con intestazione: "Roberto Malini — Cognitive Logic — QEN — Quantificazione Etica Naturale")
- [ ] **Allegato J** — `AllegatoJqen_context.pdf` — `qen_context.py`, versione Diamante 26.0, 12/06/2026 (9 pag.)
- [ ] **Codice_QEN.pdf** — `QEN_Generatore_Report.ipynb` — notebook Jupyter generatore report PDF (13 pag.)
- [ ] `graph_expanded.json` (estratto)

**Formato stampa — footer obbligatorio:**
```
© 2026 Roberto Malini | Cognitive Logic | QEN — Quantificazione Etica Naturale
Data di creazione: 25–26 maggio 2026
Ubicazione deployment: Hetzner VPS `cognitive-node-01` (178.104.190.107)
```

### 4.2 Documentazione Progettuale
- [ ] **Allegato F** — `AllegatoFCOPILOT_API.pdf` — Documentazione API QEN Copilot v1.0 — **etichettato "ALLEGATO AL DOSSIER NOTARILE QEN FRAMEWORK"** (6 pag.) — 328 nodi knowledge graph, verticali FOOD/BALNEARE/PMI
- [ ] **Allegato H** — `AllegatoHQEN_FRAMEWORK_SPEC.pdf` — QEN Framework Specification v2.0, 12/06/2026 (5 pag.)
- [ ] **MANUALE_TECNICO_OPERATIVO_MOTORE_QEN_v1.0_.pdf** — Architettura motore, dashboard, compliance filter (6 pag.)
- [ ] **QEN_ALGORITMO.pdf** — Prima stesura manuale operativo, **data: 20 gennaio 2026** (2 pag.) — documento più antico del framework
- [ ] **QEN_ARCHITETTURA_RICONCILIAZIONE.pdf** — Architettura riconciliazione multi-source, maggio 2026, CognitiveLogic × CNA Bologna (27 pag.) — sostituisce il generico `RECONCILIATION_PROTOCOL.md`
- [ ] **GLM_EVIDE_Integration_Strategy.pdf** — Strategia integrazione Governance Layer Manifest + Evidentiary Registry, 14/06/2026, v1.0 (4 pag.)
- [ ] `INFRASTRUCTURE_SPEC.md` (stampa, 2–3 pagine)

### 4.3 Prove di Deployment
- [ ] Screenshot della console Hetzner (IP, hostname, data di creazione)
- [ ] Screenshot di GitHub repo commit history (`CognitiveLogic2026`)
- [ ] Log di deploy (da `/root/cognitive-logic-api/deploy.log`)
- [ ] Email di conferma ANTHROPIC_API_KEY setup (date-stamped)

### 4.4 Documentazione di Progetto
- [ ] `CNA_BOLOGNA_OUTREACH.md` (strategia commerciale, dimostra ecosistema operativo)
- [ ] QEN Academia Proposal (istituzionale, 3–5 pagine)
- [ ] Slide di presentazione QEN — Quantificazione Etica Naturale (opzionale, ma consigliato per contesto)

### 4.5 Prova di Titolarità Intellettuale
- [ ] **Data_Must_Be.pdf** — Manifesto fondativo Cognitive Logic (1 pag.): *"Beyond the graphical interface: data must be intelligible, transparent, and immediately operational for autonomous agents."* — documento di visione originale, prova della filosofia progettuale dell'autore
- [ ] Copia della P.IVA opening (una volta acquisita)
- [ ] Certificato di dominio cognitivelogic.it (WHOIS proof o certificate)
- [ ] Elenco di lavori precedenti che dimostrano traiettoria (optional: link Fuorimenu Substack, LinkedIn)

### 4.6 CARTELLA 09 — Screenshots Datati (8 giugno 2026)
**Deposito opere per certificazione anteriorità QEN — Quantificazione Etica Naturale**

Questa cartella costituisce prova documentale fotografica con data certa. Tutti gli screenshot sono stati acquisiti in data 8 giugno 2026 e riportano data/ora visibile del dispositivo.

| File | Data/Ora | Contenuto | Valore legale |
|------|----------|-----------|---------------|
| `S1_github_repository_20260608.png` | 8 giu 2026 ore 22:47 | Repository GitHub CognitiveLogic2026 — 493 commit, struttura cartelle | Prova di sviluppo continuativo e pubblico |
| `S2_profilo_roberto_bob_malini_20260608.png` | 8 giu 2026 ore 22:53 | Profilo GitHub Roberto Bob Malini — AI Data Architect & Founder Cognitive Logic | Identità pubblica autore su piattaforma terza certificata |
| `S3_homepage_cognitivelogic_20260608.png` | 8 giu 2026 ore 23:15 | Homepage https://cognitivelogic.it — "Intelligenza artificiale misurabile" | Sito live e pubblico con design Diamante 26.0 (URL visibile) |
| `S4_bing_webmaster_sitemap_20260608.png` | 8 giu 2026 ore 23:18 | Microsoft Bing Webmaster Tools — prima submission sitemap: **25/02/2026** | **PROVA DI ANTERIORITÀ PUBBLICA** certificata da Microsoft — data certa terza parte |
| `S5a_whois_cognitivelogic_intro_20260608.png` | 8 giu 2026 ore 23:19 | WHOIS cognitivelogic.it — IP 185.199.111.153 (GitHub Pages CDN) | Conferma dominio registrato e attivo |
| `S5b_whois_cognitivelogic_created_20260608.png` | 8 giu 2026 ore 23:19 | WHOIS cognitivelogic.it — **Created: November 11, 2025** | **DATA PIÙ ANTICA** — dominio registrato 7 mesi prima del deposito notarile |

**Nota per il notaio:** Lo screenshot S4 (Bing Webmaster Tools) dimostra che il sito cognitivelogic.it era indicizzato pubblicamente già al **25 febbraio 2026**, per effetto della prima submission della sitemap. Tale dato è certificato da Microsoft Corporation, soggetto terzo indipendente rispetto all'autore. Lo screenshot S5b dimostra che il dominio cognitivelogic.it era registrato dal **11 novembre 2025**, come risulta dal database WHOIS internazionale.

---

## 5. DICHIARAZIONI SOTTOSCRITTORE (da redigere con notaio)

Il sottoscritto, **Roberto Malini**, dichiara:

1. Di essere il creatore originale e unico autore del framework QEN in tutte le sue componenti (codice, metodologia, documentazione, infrastruttura)

2. Di aver sviluppato il framework completamente in modo indipendente, senza utilizzo di opere pre-esistenti protette da diritti terzi (salvo librerie open-source dichiarate, come FastAPI, Python standard library, Claude API che rimangono property dei rispettivi titolari)

3. Che la data di creazione concettuale risale all'inizio del 2026, con completamento e deployment in produzione al 25–26 maggio 2026

4. Che il framework è stato sviluppato presso infrastruttura di proprietà (VPS Hetzner affittato) utilizzando API commerciali (Anthropic Claude Sonnet)

5. Che nessuna parte del framework è stata divulgata pubblicamente prima della presente autenticazione, eccetto:
   - Comunicazioni interne con partner CNA Bologna (NDA in place)
   - Documentazione GitHub in repo privato

6. Che richiede la certificazione di data certa e autenticità ai fini di:
   - Protezione della proprietà intellettuale
   - Supporto per eventuale registrazione SIAE
   - Fondamento per domanda di marchio UE "QEN"
   - Protezione da rivendicazioni terze di originalità

---

## 6. RICHIESTA FORMALE AL NOTAIO

**Atto richiesto:** Autenticazione di documento e certificazione di data certa

**Specifiche:**
- [ ] Sottoscrizione del presente dossier (o sommario descrittivo) da parte di Roberto Malini
- [ ] Timbro e firma del notaio con data autentica
- [ ] Rilascio di copia autentica su carta (minimo 3 copie)
- [ ] Eventuale copia digitale (PDF autenticato)

**Destinazione copie:**
1. **Copia #1:** Archivio personale (banca dati IP)
2. **Copia #2:** Preparazione registrazione SIAE
3. **Copia #3:** Supporto per marchio UE (EUIPO)

---

## 7. TIMELINE E CHECKLIST DI PREPARAZIONE

### Settimana 1 (27 maggio — 2 giugno)
- [ ] Confermare nome studio notarile a Bologna
- [ ] Prenotare appuntamento (preferibilmente 2–3 giorni lavorativi)
- [ ] Stampare tutti i file del dossier
- [ ] Preparare originali su supporto fisico

### Giorno di incontro con notaio
- [ ] Presentazione verbale del framework (5–10 min)
- [ ] Consegna dossier stampato
- [ ] Sottoscrizione atto
- [ ] Pagamento (€300 circa)
- [ ] Ritiro copie autenticate

### Entro 1 settimana post-notaio
- [ ] Iniziare processo SIAE (con copia notarile)
- [ ] Inviare comunicazione a CNA Bologna confermando protezione legale

---

## 8. NOTE TATTICHE

**Linguaggio con il notaio:**
- Usa termini precisi: "framework semantico", "metodologia proprietaria", "infrastruttura cloud"
- Enfatizza: questo NON è solo software, è una metodologia integrata (codice + scoring + knowledge graph)
- Evidenzia: deployment live in produzione = proof of concept completato

**Red flags da evitare:**
- Non dire "lavoro in progress" — dì "MVP completato"
- Non dubitare sulla data — sii assertivo
- Non nominare SIAE o marchio UE al notaio (lui fa il suo lavoro, punto)

**Budget:**
- Stima: €250–350
- Chiedi costo totale PRIMA di firmare

---

## 9. FOLLOW-UP IMMEDIATO POST-NOTAIO

```
Subject: [Cognitive Logic] Autenticazione notarile completata — prossimi step

Destinatario: info@cognitivelogic.it (tuo archivio)

Con la presente comunico che il framework QEN è stato autenticato 
presso notaio [NOME STUDIO] il [DATA].

Copie autenticate allegate.

Prossimi step:
1. Registrazione SIAE — inizio [DATA prevista]
2. Marchio UE "QEN" — timeline: [DATA target]
3. Comunicazione CNA Bologna — sottolineare protezione IP

---
```

---

**Documento preparato:** 27 maggio 2026 — **aggiornato 18 giugno 2026**  
**Per:** Roberto Malini (CF: MLNRRT62H06A944U), Founder & CVO — Cognitive Logic  
**Residenza:** Via Della Costituzione 11, 40033 Casalecchio di Reno (BO)  
**Versione:** 1.2  
**Sigla registrata:** QEN — Quantificazione Etica Naturale (IT) | Quantifying Ethical Network (EN)  
**Data più antica documentata:** 11 novembre 2025 (WHOIS dominio cognitivelogic.it)
