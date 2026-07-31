# ENTERPRISE INFORMATION ARCHITECTURE REVIEW

**Project:** Cognitive Logic
**Programme:** Commercial Evolution 1.0
**Phase:** 6 — Commercial Website Evolution
**Sprint:** 5.0
**Document ID:** EIAR-001
**Version:** 1.0
**Status:** Approved Baseline
**Repository:** /app/cognitivelogic
**Branch:** main

---

# Executive Summary

Questo documento costituisce la revisione architetturale ufficiale della Information Architecture del sito commerciale di Cognitive Logic.

Non introduce modifiche implementative.

Non modifica il design system.

Non modifica il codice HTML.

Non modifica il CSS.

Non modifica il funnel commerciale.

Il documento definisce esclusivamente l'architettura informativa, la governance della navigazione, i principi di organizzazione dei contenuti e la roadmap evolutiva che guiderà gli sprint successivi della Phase 6.

L'obiettivo è garantire che il sito possa evolvere come piattaforma Enterprise Launch Ready mantenendo coerenza architetturale, scalabilità, tracciabilità e governance.

---

# 1. Purpose

L'Enterprise Information Architecture Review ha lo scopo di:

- analizzare la struttura attuale del sito;
- verificare la coerenza dell'architettura informativa;
- definire i principi architetturali ufficiali;
- descrivere il modello di navigazione;
- formalizzare il funnel commerciale;
- definire le regole di crescita del repository;
- identificare le aree di miglioramento;
- costituire la baseline architetturale degli sprint successivi.

---

# 2. Scope

La revisione comprende esclusivamente:

- struttura informativa;
- gerarchia delle pagine;
- organizzazione dei contenuti;
- percorsi di navigazione;
- architettura dei collegamenti interni;
- modello di conversione;
- architettura SEO;
- architettura della fiducia (Trust Architecture);
- governance dei contenuti.

Sono esclusi:

- redesign grafico;
- modifiche al design system;
- modifiche responsive;
- modifiche CSS;
- modifiche JavaScript;
- nuove funzionalità.

---

# 3. Architectural Context

Il sito rappresenta il punto di accesso istituzionale al sistema Cognitive Logic.

L'architettura attuale è organizzata attorno ai seguenti domini funzionali:

- Homepage istituzionale
- Framework
- Enterprise Services
- Assessment
- Validation Programme
- Case Studies
- Enterprise Engagement
- Contact
- Research
- International Watch

Il repository contiene inoltre documentazione enterprise relativa a:

- Enterprise Service Catalogue
- Enterprise Delivery Framework
- QEN Sovereign Intelligence
- Validation Programme
- Commercial Evolution
- Website Roadmap

L'obiettivo evolutivo consiste nel trasformare il sito in una piattaforma enterprise orientata alla commercializzazione dei servizi di AI Governance, Knowledge Governance e Decision Intelligence.

---

# 4. Architectural Principles

L'intera architettura dovrà rispettare i seguenti principi.

## 4.1 Governance First

Ogni componente deve essere governabile.

---

## 4.2 Trust First

La fiducia precede la conversione.

---

## 4.3 Evidence First

Ogni affermazione deve poter essere supportata da evidenze pubbliche.

---

## 4.4 Explainability

Ogni servizio deve essere comprensibile.

---

## 4.5 Traceability

Ogni percorso deve essere tracciabile.

---

## 4.6 Scalability

La crescita non deve richiedere ristrutturazioni.

---

## 4.7 Enterprise Consistency

Ogni nuova pagina dovrà rispettare:

- design system;
- palette;
- tipografia;
- CTA;
- metadata;
- JSON-LD;
- SEO;
- governance documentale.

---

# 5. Website Architecture

L'architettura corrente è composta da cinque livelli.

## Layer 1

Institutional Presence

- Homepage
- About
- Contact

---

## Layer 2

Knowledge

- Framework
- Research
- International Watch

---

## Layer 3

Commercial

- Services
- Assessment
- Engagement

---

## Layer 4

Evidence

- Validation
- Case Studies
- Coste360

---

## Layer 5

Governance

Repository pubblico

Documentazione

Framework

Assessment

Roadmap

Trust (da introdurre nello Sprint 5.1)

---

# 6. Navigation Model

La navigazione principale deve mantenere una struttura lineare.

Home

↓

Framework

↓

Services

↓

Assessment

↓

Validation

↓

Case Studies

↓

Engagement

↓

Research

↓

Trust Center (Sprint 5.1)

↓

Contact

La struttura dovrà evitare percorsi ridondanti e mantenere una progressione logica dal contenuto informativo alla conversione.

---

# 7. Navigation Governance

La navigazione dovrà rispettare le seguenti regole.

- massimo livello di profondità: 3;
- nessuna pagina orfana;
- ogni pagina raggiungibile entro tre clic;
- presenza costante del menu principale;
- footer uniforme;
- collegamenti coerenti tra le sezioni.

Le verifiche effettuate nello Sprint 5.0 evidenziano alcune difformità nella navigazione tra pagine istituzionali e pagine legacy, che saranno oggetto di normalizzazione negli sprint successivi senza alterare la struttura consolidata del sito.

---

# 8. Current Architecture Assessment

L'analisi del repository evidenzia i seguenti punti di forza.

## Strengths

- Design system consolidato.
- Repository pulito.
- Funnel commerciale implementato.
- Metadata principali presenti.
- Canonical uniformati sul dominio principale.
- JSON-LD presente nelle pagine principali.
- Architettura documentale enterprise consolidata.
- Framework e servizi chiaramente separati.

## Improvement Areas

- introduzione del Trust Center;
- uniformazione completa delle CTA;
- implementazione dei breadcrumb;
- completamento della strategia hreflang;
- estensione dei dati strutturati alle pagine secondarie;
- consolidamento dell'Internal Linking Architecture;
- revisione completa della sitemap nella fase SEO.

---# 9. Commercial Funnel

L'architettura commerciale del sito è progettata per accompagnare il visitatore lungo un percorso progressivo di acquisizione della fiducia.

Il funnel ufficiale è definito come segue.

```
DISCOVER
      ↓
UNDERSTAND
      ↓
ASSESS
      ↓
VERIFY
      ↓
TRUST
      ↓
ENGAGE
      ↓
CONTACT
```

## Discover

Obiettivo:

far comprendere immediatamente la natura del framework.

Pagine principali:

- Home
- Framework
- Research

---

## Understand

Obiettivo:

trasformare la curiosità in comprensione.

Pagine:

- Framework
- Services
- Research
- Methodology

---

## Assess

Obiettivo:

far comprendere il valore degli assessment.

Pagine:

- Assessment

---

## Verify

Obiettivo:

dimostrare la credibilità.

Pagine:

- Validation
- Case Studies
- Coste360

---

## Trust

Obiettivo:

costruire fiducia istituzionale.

Elemento previsto:

Trust Center

(Sprint 5.1)

---

## Engage

Obiettivo:

trasformare l'interesse in relazione.

Pagina:

Enterprise Engagement

---

## Contact

Ultimo passo del funnel.

Pagina:

Contact

---

# 10. Conversion Architecture

La conversione dovrà essere costruita secondo un modello progressivo.

## Awareness

Home

↓

## Understanding

Framework

↓

## Capability

Services

↓

## Assessment

Assessment

↓

## Validation

Validation

↓

## Trust

Trust Center

↓

## Engagement

Enterprise Engagement

↓

## Contact

Contatti

Ogni pagina dovrà contribuire al passaggio verso la fase successiva.

---

# 11. CTA Hierarchy

Le Call To Action dovranno seguire una gerarchia unica.

## Livello 1

Assessment

CTA primaria.

---

## Livello 2

Validation

---

## Livello 3

Trust Center

---

## Livello 4

Enterprise Engagement

---

## Livello 5

Contact

---

Ogni pagina dovrà contenere:

- una CTA primaria;
- una CTA secondaria;
- almeno un cross-link coerente con il funnel.

---

# 12. Internal Linking Architecture

I collegamenti interni costituiscono parte integrante dell'architettura.

Principi.

Ogni pagina dovrà:

- ricevere link;
- generare link;
- contribuire alla distribuzione dell'autorità;
- evitare pagine isolate.

L'analisi del repository evidenzia una buona densità di collegamenti interni nelle pagine principali, ma anche la presenza di pagine legacy con strutture di navigazione differenti. Tali differenze saranno armonizzate progressivamente.

---

# 13. Trust Architecture

La fiducia costituisce il principale fattore di conversione.

L'architettura della fiducia sarà costruita attraverso:

- metodologia pubblica;
- framework;
- evidenze;
- repository GitHub pubblico;
- documentazione;
- explainability;
- traceability;
- governance;
- validazione;
- casi studio;
- roadmap.

Ogni elemento dovrà contribuire alla dimostrazione della maturità metodologica di Cognitive Logic.

---

# 14. Trust Center Blueprint

Lo Sprint 5.1 introdurrà una nuova pagina dedicata.

La pagina Trust Center dovrà contenere almeno:

- Visione istituzionale;
- Repository pubblico;
- Governance;
- Explainability;
- Traceability;
- Evidence;
- Timeline del progetto;
- Metriche di fiducia;
- Framework pubblicati;
- Programma di validazione;
- Documentazione disponibile;
- Collegamenti ai principali documenti;
- CTA verso Assessment;
- CTA verso Engagement;
- CTA verso Contact.

Il Trust Center diventerà il punto centrale della Trust Architecture del sito.

---

# 15. Navigation Governance

Ogni modifica futura dovrà rispettare:

- nessuna duplicazione della navigazione;
- menu coerenti;
- footer uniforme;
- link verificati;
- CTA uniformate;
- percorsi prevedibili;
- massima accessibilità.

La governance della navigazione dovrà essere documentata prima di qualsiasi modifica strutturale.

---# 16. SEO Information Architecture

L'architettura informativa costituisce la base della strategia SEO del sito.

I principi adottati sono:

- una pagina per ogni intento di ricerca primario;
- URL descrittivi e stabili;
- titoli univoci;
- meta description dedicate;
- collegamenti interni coerenti;
- struttura gerarchica facilmente interpretabile;
- canonical uniformati;
- utilizzo di dati strutturati;
- sitemap aggiornata;
- robots coerente con la strategia di indicizzazione.

L'analisi del repository conferma una buona base tecnica già implementata, sulla quale potranno essere introdotti miglioramenti incrementali senza alterare l'architettura esistente.

---

# 17. Structured Data Governance

I dati strutturati rappresentano un elemento essenziale dell'architettura informativa.

Le regole di governance prevedono che:

- le pagine istituzionali mantengano markup JSON-LD appropriato;
- i nuovi contenuti adottino il tipo di schema più idoneo;
- i dati strutturati siano coerenti con il contenuto realmente pubblicato;
- eventuali estensioni (ad esempio BreadcrumbList o FAQ) siano introdotte solo quando supportate dalla struttura della pagina.

---

# 18. Hreflang Strategy

L'internazionalizzazione del sito dovrà essere governata attraverso una strategia uniforme.

Obiettivi:

- coerenza tra versioni linguistiche;
- corretta dichiarazione delle varianti disponibili;
- utilizzo di `x-default` ove applicabile;
- eliminazione di riferimenti incoerenti;
- copertura progressiva delle pagine destinate al pubblico internazionale.

L'analisi dello Sprint 5.0 evidenzia una copertura parziale della strategia hreflang, che verrà completata negli sprint dedicati alla SEO internazionale.

---

# 19. Breadcrumb Strategy

Attualmente non è presente una strategia completa per i breadcrumb.

L'introduzione dei breadcrumb dovrà:

- migliorare la comprensione della gerarchia del sito;
- facilitare la navigazione;
- aumentare la leggibilità per i motori di ricerca;
- consentire l'adozione del markup `BreadcrumbList`.

La loro implementazione è pianificata come evoluzione architetturale e non rappresenta una criticità bloccante per il rilascio corrente.

---

# 20. Information Governance Rules

Ogni nuova pagina dovrà rispettare le seguenti regole.

## Naming

Titoli coerenti con il dominio funzionale.

## URL

URL permanenti, leggibili e privi di ridondanze.

## Metadata

Ogni pagina dovrà possedere metadati completi e univoci.

## Internal Linking

Ogni nuova pagina dovrà essere integrata nella rete dei collegamenti interni.

## Navigation

La navigazione dovrà mantenere coerenza con la gerarchia istituzionale del sito.

## Governance

Ogni modifica significativa dovrà essere documentata nel repository.

---

# 21. Findings

Durante la revisione sono stati osservati i seguenti elementi.

## Strengths

- repository ordinato;
- funnel commerciale già implementato;
- architettura delle pagine principali coerente;
- design system uniforme;
- struttura modulare facilmente estendibile;
- documentazione enterprise consolidata;
- governance documentale già presente.

## Improvement Opportunities

- introduzione del Trust Center;
- completamento della copertura hreflang;
- estensione dei dati strutturati;
- introduzione dei breadcrumb;
- ulteriore consolidamento dell'architettura dei collegamenti interni;
- armonizzazione di alcuni elementi di navigazione presenti nelle pagine legacy.

Tali elementi rappresentano opportunità di miglioramento e non compromettono la qualità complessiva dell'architettura attuale.

---

# 22. Sprint 5.0 Outcome

Lo Sprint 5.0 produce i seguenti risultati.

- Formalizzazione della Information Architecture.
- Definizione della Navigation Governance.
- Definizione della Conversion Architecture.
- Definizione della CTA Hierarchy.
- Definizione della Trust Architecture.
- Individuazione delle aree evolutive.
- Costituzione della baseline per gli sprint successivi della Phase 6.

---

# 23. Next Steps

Gli sprint successivi saranno orientati a:

1. introduzione del Trust Center;
2. consolidamento della Trust Architecture;
3. ottimizzazione della navigazione;
4. estensione dell'architettura SEO;
5. miglioramento dell'internal linking;
6. incremento della conversione;
7. evoluzione progressiva dell'esperienza enterprise mantenendo piena compatibilità con la struttura esistente.

---

# Conclusion

La revisione dell'Enterprise Information Architecture conferma che il sito Cognitive Logic dispone di una struttura informativa solida, coerente con gli obiettivi istituzionali e commerciali del progetto.

L'architettura attuale costituisce una base adeguata per l'evoluzione verso una piattaforma enterprise orientata alla governance dell'intelligenza artificiale, alla valorizzazione delle evidenze prodotte dal framework QEN Sovereign Intelligence e alla commercializzazione dei servizi di Cognitive Logic.

Le opportunità di miglioramento individuate saranno affrontate negli sprint successivi secondo un approccio incrementale, preservando la stabilità del repository, la qualità documentale e la continuità dell'esperienza utente.

---

**End of Document**
