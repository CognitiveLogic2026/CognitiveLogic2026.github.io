# ERM-001 — Enterprise Relationship Model

Status: PROPOSED
Implementation Authorized: NO

## Purpose

Definire le relazioni semantiche comuni tra le entità della Cognitive Logic Enterprise Platform.

## Relationship Principles

- Ogni relazione deve avere una direzione esplicita.
- Ogni relazione deve avere un significato documentato.
- Le relazioni non devono sostituire le evidenze.
- Le relazioni inferite devono essere distinguibili da quelle documentate.
- Le relazioni temporali devono poter essere aggiornate.
- Le relazioni critiche devono essere collegate a una fonte.

## Core Relationships

### references

Un asset richiama o menziona un'altra entità.

Esempio:

Publication → references → Regulation

### cites

Una pubblicazione cita formalmente una fonte o un'altra pubblicazione.

### evidences

Un'evidenza supporta un fatto, una decisione o una dichiarazione.

### derived_from

Un asset deriva da un altro asset, metodologia o fonte.

### governed_by

Un asset, processo o decisione è disciplinato da una regola, standard o decisione.

### belongs_to

Un'entità appartiene a un dominio, categoria, programma o raccolta.

### related_to

Relazione generale, da usare solo quando non esiste una relazione più precisa.

### explains

Una pubblicazione, metodologia o concetto spiega un'altra entità.

### defines

Uno standard, framework o documento definisce un concetto o requisito.

### applies_to

Una norma, metodologia, soluzione o controllo si applica a un settore, asset o organizzazione.

### supports

Un asset, servizio o evidenza supporta un processo, una decisione o una capacità.

### addresses

Un servizio, soluzione o controllo affronta un problema, rischio o obbligo.

### mitigates

Un controllo o una soluzione riduce un rischio.

### complies_with

Un asset o processo dichiara conformità documentata rispetto a uno standard o requisito.

La relazione non deve essere usata senza evidenza verificabile.

### implemented_by

Una metodologia, decisione o requisito è realizzato mediante un componente, processo o servizio.

### offered_as

Una capacità metodologica o tecnica è resa disponibile come servizio o soluzione.

### used_in

Un framework, metodo o tecnologia viene utilizzato in un progetto, pubblicazione o caso studio.

### produced_by

Un asset è prodotto da una persona, organizzazione, processo o sistema.

### authored_by

Una pubblicazione è attribuita a uno o più autori.

### published_by

Una pubblicazione è pubblicata da un'organizzazione o piattaforma.

### monitored_by

Un tema, sviluppo o fonte è seguito da un osservatorio o processo di monitoraggio.

### updates

Un asset modifica o aggiorna un asset precedente.

### supersedes

Un asset sostituisce formalmente un asset precedente.

### invalidates

Un'evidenza o decisione rende non più valida una precedente affermazione o relazione.

### depends_on

Un asset, servizio o processo dipende da un'altra entità.

### part_of

Un elemento costituisce parte strutturale di un sistema, programma o pubblicazione.

### applicable_in

Una norma, soluzione o metodologia è applicabile in una giurisdizione o settore.

## Relationship Metadata

Ogni relazione dovrebbe poter includere:

- relationship_id;
- source_entity;
- relation_type;
- target_entity;
- evidence_reference;
- authority;
- confidence;
- valid_from;
- valid_to;
- status;
- created_at;
- updated_at;
- governance_reference.

## Evidence Levels

### Documented

Relazione esplicitamente supportata da una fonte verificabile.

### Governed

Relazione approvata attraverso una decisione architetturale o di governance.

### Observed

Relazione rilevata attraverso osservazione documentata.

### Inferred

Relazione prodotta mediante ragionamento o analisi.

Le relazioni inferite devono essere segnalate come tali.

## Prohibited Practices

- Relazioni non definite.
- Uso indiscriminato di related_to.
- Dichiarazioni di conformità senza evidenza.
- Confusione tra correlazione e causalità.
- Confusione tra fonte e interpretazione.
- Relazioni commerciali presentate come fatti indipendenti.
- Inferenze rappresentate come evidenze.

## Constraints

- Nessuna implementazione.
- Nessuna modifica al grafo esistente.
- Nessuna modifica al sito.
- Nessun commit.
- Nessun push.
