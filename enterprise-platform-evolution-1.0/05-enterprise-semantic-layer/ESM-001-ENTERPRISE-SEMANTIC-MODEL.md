# ESM-001 — Enterprise Semantic Model

Status: PROPOSED
Implementation Authorized: NO

## Purpose

Integrare entità, relazioni, tassonomie, evidenze e regole semantiche in un modello comune per l'intero ecosistema Cognitive Logic.

## Semantic Foundation

Il modello semantico si basa su:

- EPAE-001 Enterprise Platform Architecture;
- CPA-001 Commercial Platform Architecture;
- KPA-001 Knowledge Platform Architecture;
- EIM-001 Enterprise Information Model;
- EEM-001 Enterprise Entity Model;
- ERM-001 Enterprise Relationship Model;
- ETM-001 Enterprise Taxonomy Model;
- QEN Framework;
- governance corpus esistente.

## Semantic Layers

### Identity Layer

Definisce l'identità stabile di:

- entità;
- asset;
- pubblicazioni;
- servizi;
- decisioni;
- evidenze.

### Classification Layer

Applica:

- domini;
- tipi;
- categorie;
- temi;
- settori;
- stati;
- giurisdizioni.

### Relationship Layer

Descrive le relazioni esplicite tra entità e asset.

### Evidence Layer

Collega fatti, dichiarazioni, decisioni e relazioni alle rispettive fonti.

### Governance Layer

Collega asset e processi a:

- decisioni;
- standard;
- approvazioni;
- responsabilità;
- stato di validità.

### Temporal Layer

Rappresenta:

- data di pubblicazione;
- periodo di validità;
- aggiornamenti;
- sostituzioni;
- deprecazioni;
- evoluzioni normative.

### Authority Layer

Distingue:

- fonte primaria;
- fonte istituzionale;
- fonte secondaria;
- osservazione;
- analisi Cognitive Logic;
- inferenza QEN.

## Semantic Assertions

Ogni affermazione rilevante dovrebbe poter essere rappresentata come:

```text
Subject
→ Predicate
→ Object
→ Evidence
→ Authority
→ Validity
→ Governance Status
cd /app/cognitivelogic || exit 1

set -e

STANDARDS_DIR="enterprise-platform-evolution-1.0/07-cross-platform-standards"
ROADMAP_DIR="enterprise-platform-evolution-1.0/08-enterprise-roadmap"
REGISTER="enterprise-platform-evolution-1.0/00-governance/ENTERPRISE-PLATFORM-DOCUMENT-REGISTER.md"

mkdir -p "$STANDARDS_DIR" "$ROADMAP_DIR"

echo "======================================================"
echo "ENTERPRISE CROSS-PLATFORM STANDARDS"
echo "DOCUMENTATION ONLY — NO SITE IMPLEMENTATION"
echo "======================================================"

cat > "$STANDARDS_DIR/ELS-001-EDITORIAL-TO-COMMERCIAL-LINKING-STANDARD.md" <<'EOF'
# ELS-001 — Editorial-to-Commercial Linking Standard

Status: PROPOSED
Implementation Authorized: NO

## Purpose

Definire le regole con cui i contenuti editoriali di Cognitive Logic possono collegarsi a servizi, soluzioni e verticali commerciali senza compromettere indipendenza, autorevolezza e integrità editoriale.

## Scope

Lo standard si applica a:

- International Watch;
- Research;
- Knowledge Base;
- Insights;
- Case Studies;
- pagine servizi;
- pagine soluzioni;
- pagine verticali;
- materiali per partnership e network professionali.

## Core Principle

Il contenuto editoriale costruisce autorevolezza attraverso qualità, evidenze e metodo.

Il collegamento commerciale deve essere:

- pertinente;
- trasparente;
- contestuale;
- proporzionato;
- verificabile;
- non invasivo.

## Editorial Independence Rules

### International Watch

International Watch deve mantenere funzione di osservatorio internazionale governato.

Sono ammessi:

- collegamenti a Research;
- collegamenti alla Knowledge Base;
- collegamenti a metodologie pertinenti;
- collegamenti discreti a servizi direttamente correlati al tema.

Non sono ammessi:

- call to action aggressive;
- promesse commerciali;
- offerte non pertinenti;
- alterazione dei fatti per sostenere una proposta commerciale;
- trasformazione dell'articolo in landing page promozionale.

### Research

Research deve mantenere:

- indipendenza metodologica;
- citabilità;
- separazione tra risultati e offerta commerciale;
- dichiarazione dei limiti;
- tracciabilità delle fonti.

Sono ammessi collegamenti a:

- metodologia QEN;
- applicazioni professionali;
- servizi di assessment;
- workshop;
- casi studio correlati.

### Knowledge Base

La Knowledge Base può collegare concetti e obblighi a:

- metodologie;
- strumenti;
- servizi;
- soluzioni;
- contenuti di approfondimento.

Il collegamento deve aiutare la comprensione, non interromperla.

### Insights

Insights può avere una funzione più vicina al decision support.

Può includere:

- implicazioni per imprese;
- rischi;
- priorità operative;
- possibili percorsi di assessment;
- collegamenti a servizi pertinenti.

### Case Studies

Case Studies può dimostrare applicazioni concrete.

Deve distinguere:

- problema;
- contesto;
- metodologia;
- attività svolte;
- evidenze;
- risultati;
- limiti;
- elementi non generalizzabili.

## Permitted Linking Patterns

### Editorial to Editorial

Esempio:

International Watch
→ Research
→ Knowledge Base
→ Case Study

### Editorial to Methodology

Esempio:

Research
→ QEN Framework
→ Methodology
→ Governance Model

### Editorial to Commercial

Esempio:

Insight
→ AI Governance Assessment

La relazione deve essere semanticamente pertinente.

### Commercial to Editorial

Esempio:

Service Page
→ Research Paper
→ International Watch Source
→ Knowledge Base Definition

Le pagine commerciali devono utilizzare contenuti editoriali come evidenze, non come decorazione.

## Commercial Link Types

Ogni collegamento commerciale dovrebbe essere classificato come:

- Related Service;
- Related Solution;
- Assessment Path;
- Training Opportunity;
- Sector Application;
- Methodology Application;
- Partnership Opportunity.

## Call-to-Action Standard

Le call to action editoriali devono essere sobrie.

Formulazioni ammesse:

- Approfondisci la metodologia.
- Esplora l'applicazione settoriale.
- Consulta il servizio correlato.
- Richiedi un assessment preliminare.
- Esamina il modello di governance.

Formulazioni da evitare:

- Garantisci la conformità.
- Elimina ogni rischio.
- Diventa subito conforme.
- Soluzione definitiva.
- Risultati garantiti.

## Evidence Requirement

Ogni collegamento tra contenuto e offerta deve essere supportato da almeno uno dei seguenti elementi:

- metodologia documentata;
- competenza dimostrabile;
- ricerca pubblicata;
- applicazione verificata;
- decisione architetturale;
- caso studio autorizzato;
- asset tecnico esistente.

## Placement Rules

I collegamenti commerciali possono apparire:

- al termine del contenuto;
- in un box di approfondimento;
- in una sezione Related Services;
- in una sezione Applications;
- all'interno di un percorso semantico pertinente.

Non devono:

- interrompere continuamente la lettura;
- precedere le evidenze principali;
- confondersi con le fonti;
- apparire come raccomandazione indipendente.

## Visual Distinction

Gli elementi commerciali devono essere distinguibili da:

- contenuto editoriale;
- citazioni;
- fonti;
- analisi QEN;
- note metodologiche.

## Governance Workflow

Ogni nuovo pattern di collegamento richiede:

Evidence
→ Analysis
→ Proposal
→ Approval
→ Implementation
→ Verification
→ Documentation

## KPI

Indicatori iniziali:

- pertinenza dei collegamenti;
- tasso di navigazione editoriale-commerciale;
- qualità del percorso informativo;
- assenza di promozione invasiva;
- copertura dei servizi da parte di evidenze;
- coerenza semantica;
- integrità editoriale.

## Constraints

- Nessuna modifica al sito.
- Nessuna aggiunta di CTA pubbliche.
- Nessuna modifica a International Watch.
- Nessuna modifica a Research.
- Nessuna modifica alla homepage.
- Nessun commit.
- Nessun push.
