# Dossier di Autenticazione Notarile — QEN Framework
## QEN — Quantificazione Etica Naturale | Cognitive Logic | Bologna, Italia

**Versione:** 2.0 — **Data:** 18 giugno 2026  
**Oggetto:** Certificazione di data certa per framework semantico QEN — Quantificazione Etica Naturale  
**Sigla ufficiale:** QEN = Quantificazione Etica Naturale (IT) / Quantifying Ethical Network (EN)  
**Data più antica documentata:** 11 novembre 2025 (registrazione dominio cognitivelogic.it — WHOIS)

---

## 1. INTESTAZIONE FORMALE

```
Richiedente:     Roberto Malini
Codice Fiscale:  MLNRRT62H06A944U
Residenza:       Via Della Costituzione 11 — 40033 Casalecchio di Reno (BO)
Finalità:        Certificazione di data certa e autenticità di opera intellettuale originale
Studio notarile: [TBD — preferibilmente Bologna / Casalecchio di Reno]
```

> **Nota identificativa:** Il richiedente è conosciuto professionalmente anche come "Roberto Bob Malini"
> ("Bob" è soprannome d'uso). Ai fini del presente atto notarile si utilizza esclusivamente il nome
> anagrafico **Roberto Malini** (CF: MLNRRT62H06A944U), al fine di distinguersi univocamente
> dall'omonimo scrittore e autore Roberto Malini attivo in ambito letterario.

---

## 2. DESCRIZIONE DELL'OPERA INTELLETTUALE

### 2.1 Titolo e Genere

**QEN Framework — Quantificazione Etica Naturale**  
Sistema proprietario di scoring etico multi-dimensionale per operatori HoReCa e PMI artigianali.

- **Genere:** Framework semantico + sistema di scoring + infrastruttura dati
- **Natura:** Software, documentazione, metodologia proprietaria
- **Stato:** MVP completato — 4 agenti live in produzione

### 2.2 Ambito di Applicazione

- **Settore:** Food ethics, sustainability governance, AI-driven compliance
- **Target:** HoReCa (ristorazione, alberghiero, balneare) e PMI artigianali
- **Geografico:** Emilia-Romagna — pilota CNA Bologna

### 2.3 Formula di Scoring

```
QEN Score = (VS × 0,40) + (VA × 0,35) + (VT × 0,25)
```

| Componente | Descrizione | Peso |
|-----------|-------------|------|
| **VS** — Valore Sociale | Diritti lavoratori, certificazioni etiche, governance HR | 40% |
| **VA** — Valore Ambientale | Efficienza energetica, gestione rifiuti, certificazioni ambientali | 35% |
| **VT** — Valore Territoriale | Radicamento filiera locale, prossimità fornitori | 25% |

- **Scala:** 0–100 punti
- **Soglia certificazione:** ≥ 75 punti

### 2.4 Cronologia Documentata — Prove di Anteriorità

| # | Data | Evento | Fonte / Prova |
|---|------|--------|---------------|
| 1 | **11 novembre 2025** | Registrazione dominio cognitivelogic.it | WHOIS internazionale — "Created: November 11, 2025" — Allegato K (S5b) |
| 2 | **20 gennaio 2026** | Prima stesura manuale operativo motore QEN | `QEN_ALGORITMO.pdf` — data intestazione — Allegato B |
| 3 | **25 febbraio 2026** | Prima indicizzazione pubblica sito | Microsoft Bing Webmaster Tools — prima submission sitemap — Allegato K (S4) |
| 4 | **25 maggio 2026** | Completamento MVP | Deploy log Hetzner VPS `cognitive-node-01` |
| 5 | **26–27 maggio 2026** | Deployment in produzione | Console Hetzner — IP 178.104.190.107 |
| 6 | **8 giugno 2026** | 493 commit GitHub certificati | Screenshot repo CognitiveLogic2026 — Allegato K (S1) |
| 7 | **12 giugno 2026** | Framework Spec v2.0 + qen_context.py Diamante 26.0 | Allegato H + Allegato J |
| 8 | **14 giugno 2026** | Strategia integrazione GLM + EVIDE v1.0 | Allegato E |
| 9 | **18 giugno 2026** | Aggiornamento e completamento dossier notarile | Presente documento v2.0 |

> **Nota legale — tre livelli di anteriorità:**
> 1. **Terza parte indipendente (WHOIS):** 11 novembre 2025 — registrazione dominio certificata dal database WHOIS internazionale
> 2. **Terza parte pubblica (Microsoft):** 25 febbraio 2026 — prima indicizzazione certificata da Bing Webmaster Tools
> 3. **Documento interno datato:** 20 gennaio 2026 — prima stesura operativa del framework (Allegato B)
>
> **Nota sulla sigla:** `QEN_ALGORITMO.pdf` (Allegato B) riporta la variante "Quantificazione dell'Etica Naturale" (con articolo contratto). La sigla ufficiale adottata in tutti i documenti successivi è **QEN — Quantificazione Etica Naturale** (senza articolo).

---

## 3. COMPONENTI TECNICHE

### 3.1 Codice Sorgente Principale

**`orchestrator.py`** — FastAPI backend (Allegato G parziale)
- Ubicazione: `/root/cognitive-logic-api/orchestrator.py` — Hetzner VPS CAX21 `cognitive-node-01`
- Lingua: Python 3.9+ — ~350–400 linee
- Endpoints: `/agents/compliance-auditor` · `/agents/territorial-mapper` · `/agents/advisory-council` · `/agents/intelligence-feed`

**`qen_context.py`** — Modulo di contesto QEN (Allegato J)
- Single source of truth per formula, pesi, soglie, modelli LLM e mapping normativi
- Versione Diamante 26.0 — 12 giugno 2026

**`QEN_Generatore_Report.ipynb`** — Notebook Jupyter generatore report PDF (Allegato G)

**`data/qen_graph_v4.json`** — Knowledge graph semantico (130 nodi, 209 edge)

### 3.2 Documentazione Metodologica

Vedi Allegati B, C, D, H per la documentazione completa del framework.

**Casi pilota documentati:**

| Operatore | Città | QEN Score |
|-----------|-------|-----------|
| Veganoo | Bologna | 79,0 |
| Colt Fragranza | Bologna | 81,2 |
| Bologna100Botteghe | Bologna | 79,5 |
| Benchmark CNA Bologna | — | 77,75 |

### 3.3 Architettura Infrastrutturale

- **Server:** Hetzner CAX21 ARM64 — `cognitive-node-01` — IP 178.104.190.107
- **Stack:** FastAPI + Claude Sonnet + JSON knowledge graph
- **CI/CD:** GitHub Actions — repo `CognitiveLogic2026/CognitiveLogic2026.github.io` — 493 commit
- **API pubblica:** `https://api.cognitivelogic.it` (Allegato F)
- **Governance manifest:** GLM/1.0 — `it.cognitivelogic.node.01` (Allegato E)

---

## 4. ALLEGATI — INDICE COMPLETO

### 4.1 Tavola Riepilogativa Allegati

| All. | File | Tipo | Data | Pag. | Note |
|------|------|------|------|------|------|
| **A** | `Data_Must_Be.pdf` | Manifesto fondativo | — | 1 | *"data must be intelligible, transparent, and immediately operational for autonomous agents"* |
| **B** | `QEN_ALGORITMO.pdf` | Prima stesura operativa | **20/01/2026** | 2 | Documento interno più antico del framework |
| **C** | `MANUALE_TECNICO_OPERATIVO_MOTORE_QEN_v1.0_.pdf` | Manuale tecnico operativo | — | 6 | Architettura motore, dashboard, compliance filter |
| **D** | `QEN_ARCHITETTURA_RICONCILIAZIONE.pdf` | Architettura riconciliazione | Mag. 2026 | 27 | CognitiveLogic × CNA Bologna — Scenario C Hybrid Smart |
| **E** | `GLM_EVIDE_Integration_Strategy.pdf` | Strategia governance | 14/06/2026 | 4 | GLM/1.0 + EVIDE/1.0 — nodo `it.cognitivelogic.node.01` |
| **F** | `AllegatoFCOPILOT_API.pdf` | Documentazione API | — | 6 | QEN Copilot v1.0 — 328 nodi — etichettato "ALLEGATO AL DOSSIER NOTARILE" |
| **G** | `Codice_QEN.pdf` | Codice sorgente | — | 13 | `QEN_Generatore_Report.ipynb` — notebook Jupyter |
| **H** | `AllegatoHQEN_FRAMEWORK_SPEC.pdf` | Specifica framework | 12/06/2026 | 5 | QEN Framework Specification v2.0 — CC BY-SA 4.0 |
| **J** | `AllegatoJqen_context.pdf` | Codice sorgente | 12/06/2026 | 9 | `qen_context.py` — versione Diamante 26.0 |
| **K** | Cartella 09 — 6 screenshot datati | Prove fotografiche | 08/06/2026 | — | Vedi sezione 4.3 |

> **Nota:** La lettera I è omessa per evitare confusione con il numero 1 nei documenti stampati. La sequenza è A–H, J, K.

### 4.2 Documenti da Stampare (senza allegato PDF dedicato)

Stampare con footer:
```
© 2026 Roberto Malini | Cognitive Logic | QEN — Quantificazione Etica Naturale
Data di creazione: 25–26 maggio 2026 | Hetzner VPS cognitive-node-01 (178.104.190.107)
```

- [ ] `orchestrator.py` — backend FastAPI (~350–400 linee)
- [ ] `data/qen_graph_v4.json` — knowledge graph (estratto rappresentativo)
- [ ] `INFRASTRUCTURE_SPEC.md` — specifica infrastruttura (2–3 pagine)

### 4.3 Prove di Anteriorità — Cartella 09 Screenshots (Allegato K)

Tutti gli screenshot acquisiti il **8 giugno 2026** con data/ora dispositivo visibile.

| Codice | File | Ora | Contenuto | Valore legale |
|--------|------|-----|-----------|---------------|
| **S1** | `S1_github_repository_20260608.png` | 22:47 | GitHub repo — 493 commit, struttura cartelle | Sviluppo continuativo e pubblico certificato |
| **S2** | `S2_profilo_roberto_bob_malini_20260608.png` | 22:53 | Profilo GitHub — AI Data Architect & Founder Cognitive Logic | Identità pubblica autore su piattaforma terza |
| **S3** | `S3_homepage_cognitivelogic_20260608.png` | 23:15 | Homepage cognitivelogic.it — "Intelligenza artificiale misurabile" | Sito live con design Diamante 26.0 — URL visibile |
| **S4** | `S4_bing_webmaster_sitemap_20260608.png` | 23:18 | Bing Webmaster — prima submission sitemap: **25/02/2026** | **ANTERIORITÀ PUBBLICA** — certificata da Microsoft Corporation |
| **S5a** | `S5a_whois_cognitivelogic_intro_20260608.png` | 23:19 | WHOIS — IP 185.199.111.153 (GitHub Pages CDN) | Dominio registrato e attivo |
| **S5b** | `S5b_whois_cognitivelogic_created_20260608.png` | 23:19 | WHOIS — **Created: November 11, 2025** | **DATA PIÙ ANTICA** — 7 mesi prima del deposito notarile |

**Nota per il notaio:**
- **S4** certifica indicizzazione pubblica al 25/02/2026 tramite Microsoft Corporation (soggetto terzo indipendente)
- **S5b** certifica registrazione dominio al 11/11/2025 tramite database WHOIS internazionale

### 4.4 Prove di Deployment

- [ ] Screenshot console Hetzner (IP, hostname, data di creazione server)
- [ ] Log di deploy: `/root/cognitive-logic-api/deploy.log`
- [ ] Email di conferma ANTHROPIC_API_KEY setup (date-stamped)

---

## 5. DICHIARAZIONI SOTTOSCRITTORE

Il sottoscritto **Roberto Malini** (CF: MLNRRT62H06A944U) dichiara:

1. Di essere il **creatore originale e unico autore** del framework QEN — Quantificazione Etica Naturale in tutte le sue componenti: codice sorgente, metodologia di scoring, knowledge graph semantico, documentazione tecnica e infrastruttura

2. Di aver sviluppato il framework in modo **completamente indipendente**, senza utilizzo di opere pre-esistenti protette da diritti terzi (salvo librerie open-source dichiarate: FastAPI, Python standard library, Claude API — che rimangono proprietà dei rispettivi titolari)

3. Che la **data di prima concettualizzazione** documentata è **20 gennaio 2026** (Allegato B — `QEN_ALGORITMO.pdf`); il completamento dell'MVP è avvenuto il **25 maggio 2026** con deployment in produzione il **26–27 maggio 2026**

4. Che il framework è stato sviluppato su **infrastruttura propria** (VPS Hetzner CAX21 ARM64 affittato) utilizzando API commerciali (Anthropic Claude Sonnet)

5. Che la **prima pubblicazione pubblica** verificabile è certificata da Microsoft Bing Webmaster Tools al **25 febbraio 2026** (Allegato K — S4)

6. Che il dominio `cognitivelogic.it` risulta registrato dal **11 novembre 2025** come da database WHOIS internazionale (Allegato K — S5b)

7. Che richiede la certificazione di data certa e autenticità ai fini di:
   - Protezione della proprietà intellettuale (L. 633/1941)
   - Registrazione SIAE — Registro Pubblico Speciale
   - Domanda di marchio UE "QEN" presso EUIPO
   - Protezione da rivendicazioni terze di originalità

---

## 6. RICHIESTA FORMALE AL NOTAIO

**Atto richiesto:** Autenticazione di documento con certificazione di data certa

- [ ] Sottoscrizione del presente dossier da parte di Roberto Malini
- [ ] Timbro e firma del notaio con data autentica
- [ ] Rilascio copia autentica cartacea — minimo 3 copie
- [ ] Copia digitale (PDF autenticato)

**Destinazione copie:**

| Copia | Destinazione |
|-------|-------------|
| #1 | Archivio personale — banca dati IP |
| #2 | Registrazione SIAE — Registro Pubblico Speciale |
| #3 | Marchio UE "QEN" — EUIPO |

**Budget stimato:** €250–350 — chiedere costo totale prima di firmare

---

## 7. CHECKLIST PREPARAZIONE

### Ante-appuntamento
- [ ] Confermare studio notarile a Bologna / Casalecchio di Reno
- [ ] Prenotare appuntamento
- [ ] Stampare Allegati A–K + documenti § 4.2
- [ ] Raccogliere prove deployment (§ 4.4)
- [ ] Preparare tutto su supporto fisico

### Giorno notaio
- [ ] Presentazione verbale framework (5–10 min)
- [ ] Consegna dossier completo stampato
- [ ] Sottoscrizione atto
- [ ] Pagamento
- [ ] Ritiro 3 copie autenticate

### Entro 1 settimana post-notaio
- [ ] Avviare registrazione SIAE (con copia notarile)
- [ ] Comunicare a CNA Bologna protezione IP attiva
- [ ] Avviare pratica EUIPO marchio "QEN"

---

## 8. NOTE OPERATIVE PER IL NOTAIO

**Linguaggio da usare:**
- "Framework semantico proprietario" — non "sito web" o "app"
- "Metodologia integrata" — codice + scoring + knowledge graph sono un'unica opera
- "MVP completato e in produzione" — non "lavoro in corso"

**Non menzionare al notaio:** SIAE, marchio UE, EUIPO — il notaio certifica la data, non valuta la strategia IP.

---

## 9. FOLLOW-UP POST-NOTAIO

```
Subject: [Cognitive Logic] Autenticazione notarile completata — QEN Framework

A: info@cognitivelogic.it (archivio personale)

Il framework QEN — Quantificazione Etica Naturale è stato autenticato
presso notaio [NOME STUDIO] in data [DATA].

Allegati: copie autenticate dossier (A–K).

Prossimi step:
1. Registrazione SIAE — Registro Pubblico Speciale — [DATA]
2. Marchio UE "QEN" — EUIPO — [DATA]
3. CNA Bologna — conferma protezione IP — [DATA]
```

---

**Documento preparato:** 27 maggio 2026 — **Versione 2.0: 18 giugno 2026**  
**Richiedente:** Roberto Malini (CF: MLNRRT62H06A944U) — Founder & CVO, Cognitive Logic  
**Residenza:** Via Della Costituzione 11, 40033 Casalecchio di Reno (BO)  
**Sigla:** QEN — Quantificazione Etica Naturale (IT) | Quantifying Ethical Network (EN)  
**Data più antica documentata:** 11 novembre 2025 — WHOIS dominio cognitivelogic.it  
© 2026 Roberto Malini | Cognitive Logic | QEN — Quantificazione Etica Naturale
