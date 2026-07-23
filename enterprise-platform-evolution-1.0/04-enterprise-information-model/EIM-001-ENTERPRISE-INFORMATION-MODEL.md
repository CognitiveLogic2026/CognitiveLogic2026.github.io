# EIM-001 — Enterprise Information Model

Status: PROPOSED
Implementation Authorized: NO

## Purpose

Definire il modello informativo comune della Cognitive Logic Enterprise Platform.

L'EIM costituisce il livello di astrazione condiviso tra:

- Editorial Platform
- Commercial Platform
- Knowledge Platform
- Technical Platform

## Enterprise Asset Categories

Ogni elemento della piattaforma appartiene a una categoria.

### Editorial Assets

- International Watch Article
- Research Paper
- Insight
- Case Study
- Knowledge Base Entry

### Commercial Assets

- Service
- Solution
- Assessment
- Workshop
- Training
- Partnership
- Industry Offering

### Knowledge Assets

- Framework
- Methodology
- Concept
- Standard
- Taxonomy
- Ontology
- Evidence
- Decision

### Technical Assets

- Repository
- API
- Component
- Copilot
- Knowledge Graph
- Runtime Service

## Common Metadata

Ogni asset deve poter essere descritto mediante:

- identifier
- asset_type
- platform_domain
- title
- description
- abstract
- author
- owner
- status
- version
- publication_date
- last_update
- language
- jurisdiction
- sectors
- topics
- entities
- keywords
- evidence_sources
- related_assets
- governance_reference
- canonical_url
- lifecycle_state

## Lifecycle States

- Draft
- Review
- Approved
- Published
- Updated
- Archived
- Deprecated

## Governance States

- Proposed
- Approved
- Active
- Superseded
- Retired

## Cross-Platform Rules

Ogni asset può essere collegato a:

- altri asset editoriali;
- servizi;
- soluzioni;
- framework;
- decisioni;
- evidenze;
- normative;
- organizzazioni.

## Design Principles

- One asset, one identifier.
- Explicit metadata.
- Explicit relationships.
- Version traceability.
- Evidence traceability.
- Semantic consistency.
- Platform independence.
- Reusability by design.

## Constraints

- Nessuna implementazione.
- Nessuna modifica al sito.
- Nessuna modifica agli URL.
- Nessun commit.
- Nessun push.
