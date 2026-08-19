# Versionamento e revisione

`schema_version` segue SemVer per il contratto; `record_version` è SemVer per il record. Correzioni non sostanziali incrementano patch; cambiamenti analitici compatibili minor; cambi di significato/scope major. I record pubblicati sono immutabili: una nuova versione usa `supersedes`, conserva `previous_assessment` dove applicabile e spiega `change_reason`.

`created_at`/`updated_at` descrivono il record; `valid_from`/`valid_until` la validità; `as_of` il limite conoscitivo; `origin_timestamp`, `publication_timestamp`, `capture_time` ed `event_time` restano distinti. Nessun valore futuro o scaduto viene esteso implicitamente.

Riesame obbligatorio per: scadenza; nuova evidenza materiale; fonte ritirata/corretta; dipendenza scoperta; contraddizione; mutamento di definizione/scope; contestazione fondata; errore di integrità/provenienza. `review_required` e `review_due` sono obbligatori. La storia non viene cancellata.
