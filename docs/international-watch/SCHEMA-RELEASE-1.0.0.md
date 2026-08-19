# International Watch schema release 1.0.0

Data: 2026-08-19. Stato: stabile, approvato metodologicamente, non pubblico e non integrato nel core QEN.

La semantica di `1.0.0-rc.1` è conservata. Rispetto alla RC sono diventati normativi: `publication_timestamp`, `source_as_at` e `accessed_at` per le fonti; motivazione dell'assenza di controevidenza; trigger di revisione dei claim. Gli stati epistemici, le definizioni e le regole d'indipendenza non cambiano.

Compatibilità: i record RC sono migrabili senza reinterpretazione analitica, ma devono aggiungere i nuovi metadati obbligatori e dichiarare `schema_version: 1.0.0`. Gli stati Fase 1 `active/archived` non appartengono al contratto stabile.

Gate: esempi, IW-001, riferimenti, workflow, test positivi e negativi, campi vietati, warning e reviewer verificati. Decisione tecnica e metodologica assistita da Codex attribuita alla funzione `Cognitive Logic — International Watch Methodology Review`. L'approvazione finale resta riservata al responsabile umano di Cognitive Logic; non vi sono indipendenza organizzativa, certificazione esterna, revisione legale specialistica o autorizzazione alla pubblicazione.
