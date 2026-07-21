# ADR-CLE — Commercial Homepage Release 1.0

## Step 3 — Enterprise Trust Block

**Data:** 2026-07-21T21:53:46+02:00
**Stato:** Approved for implementation
**Baseline:** 30ae93c
**File interessato:** `index.html`

## Contesto

La Hero commerciale e l'Enterprise Value Proposition sono già pubblicate
e costituiscono baseline immutabile.

Tra la Value Proposition e la sezione “Sezioni · Tutte le pagine” manca
un livello sintetico di fiducia enterprise che colleghi la promessa
commerciale agli asset verificabili dell'ecosistema Cognitive Logic.

## Decisione

Inserire un unico Enterprise Trust Block dopo la Value Proposition e
prima di “Sezioni · Tutte le pagine”.

Il blocco valorizza esclusivamente asset già esistenti:

- AI Governance
- Knowledge Governance
- Explainable AI
- EU AI Act Readiness
- QEN Framework
- Decision Traceability
- Knowledge Graph
- Research
- International Watch
- metodologia evidence-based
- architettura verificabile
- governance dei dati e delle decisioni

## Vincoli

Non modificare:

- Hero
- Enterprise Value Proposition
- header
- menu
- footer
- CSS
- JavaScript
- URL
- sitemap
- metadata
- JSON-LD
- Research
- International Watch

## Impatto

Aggiunta chirurgica di un solo blocco HTML semantico nella homepage.
Nessuna nuova pagina, prodotto, URL o dipendenza.
