# EEM-001 — Enterprise Entity Model

Status: PROPOSED
Implementation Authorized: NO

## Purpose

Definire le entità condivise dalla Cognitive Logic Enterprise Platform.

Il modello si applica ai domini:

- Editorial Platform
- Commercial Platform
- Knowledge Platform
- Technical Platform

## Entity Design Principles

- Ogni entità deve avere un identificatore stabile.
- Ogni entità deve avere un tipo esplicito.
- Ogni entità deve avere uno stato di governance.
- Ogni entità deve essere collegabile a fonti ed evidenze.
- Le entità non devono essere duplicate quando rappresentano lo stesso oggetto.
- Le varianti linguistiche devono riferirsi alla stessa identità semantica.

## Core Entity Classes

### Person

Rappresenta:

- autore;
- ricercatore;
- esperto;
- decisore;
- fondatore;
- relatore;
- responsabile;
- stakeholder.

Attributi minimi:

- identifier;
- preferred_name;
- role;
- affiliation;
- authority_reference;
- source_reference;
- status.

### Organization

Rappresenta:

- impresa;
- istituzione;
- autorità;
- associazione;
- università;
- centro di ricerca;
- organismo di standardizzazione;
- partner;
- cliente autorizzato.

Attributi minimi:

- identifier;
- legal_or_public_name;
- organization_type;
- jurisdiction;
- website;
- source_reference;
- status.

### Publication

Rappresenta:

- International Watch article;
- Research paper;
- Insight;
- Case Study;
- Knowledge Base entry;
- technical report;
- briefing.

Attributi minimi:

- identifier;
- title;
- publication_type;
- editorial_domain;
- author;
- publication_date;
- canonical_url;
- language;
- governance_status.

### Framework

Rappresenta:

- QEN Framework;
- framework normativo;
- framework metodologico;
- framework tecnico;
- framework di valutazione.

### Methodology

Rappresenta:

- metodo;
- processo;
- protocollo;
- modello di assessment;
- metodologia di ricerca;
- metodologia di governance.

### Concept

Rappresenta:

- concetto metodologico;
- concetto tecnico;
- concetto normativo;
- concetto editoriale;
- concetto commerciale.

### Topic

Rappresenta un argomento utilizzato per classificazione, navigazione e collegamento semantico.

### Regulation

Rappresenta:

- regolamento;
- direttiva;
- legge;
- decreto;
- linea guida istituzionale;
- obbligo normativo.

### Standard

Rappresenta:

- standard tecnico;
- standard organizzativo;
- standard editoriale;
- standard metodologico;
- specifica.

### Technology

Rappresenta:

- modello AI;
- piattaforma;
- software;
- infrastruttura;
- API;
- Knowledge Graph;
- sistema di identità;
- componente tecnico.

### Evidence

Rappresenta un elemento verificabile utilizzato per supportare:

- fatti;
- decisioni;
- analisi;
- valutazioni;
- dichiarazioni commerciali;
- risultati.

### Source

Rappresenta l'origine di un'informazione.

Tipi:

- primary source;
- secondary source;
- institutional source;
- technical source;
- internal evidence;
- observed evidence.

### Decision

Rappresenta:

- ADR;
- EDR;
- CAD;
- approval;
- architectural decision;
- governance decision;
- editorial decision.

### Service

Rappresenta una capacità professionale offerta da Cognitive Logic.

### Solution

Rappresenta una combinazione strutturata di metodologia, tecnologia e servizio.

### Industry

Rappresenta:

- settore economico;
- comparto;
- verticale;
- dominio applicativo.

### Jurisdiction

Rappresenta:

- Unione europea;
- Stato;
- Regione;
- territorio;
- ambito regolatorio.

### Risk

Rappresenta un rischio:

- normativo;
- tecnico;
- operativo;
- reputazionale;
- etico;
- informativo;
- commerciale.

### Control

Rappresenta una misura destinata a mitigare o governare un rischio.

### Obligation

Rappresenta un obbligo normativo, contrattuale, metodologico o organizzativo.

### Metric

Rappresenta:

- KPI;
- indicatore;
- score;
- misura;
- soglia;
- criterio di valutazione.

### Asset

Classe generale per:

- asset editoriale;
- asset commerciale;
- asset conoscitivo;
- asset tecnico;
- asset documentale.

## Entity Identity Rules

Ogni entità deve prevedere, quando applicabile:

- global identifier;
- preferred label;
- alternative labels;
- language;
- entity class;
- description;
- owner;
- source;
- creation date;
- last update;
- lifecycle state;
- governance state.

## Entity Resolution Rules

Prima di creare una nuova entità occorre verificare:

1. esistenza di un'entità equivalente;
2. presenza di sinonimi;
3. varianti linguistiche;
4. precedenti identificatori;
5. eventuali entità superseded;
6. fonti autorevoli disponibili.

## Constraints

- Nessuna implementazione.
- Nessuna modifica al sito.
- Nessuna modifica al Knowledge Graph runtime.
- Nessuna migrazione dati.
- Nessun commit.
- Nessun push.
