# Workflow umano International Watch

Percorso ordinario: `draft → in_review → approved → published → superseded | withdrawn`. Sono consentiti inoltre `in_review → draft` per richiesta di correzioni, `approved → in_review` per nuova evidenza materiale prima della pubblicazione e `published → in_review` soltanto mediante nuova versione che supersede il record immutabile. Ogni altra transizione è vietata.

L'autore prepara; il revisore umano verifica evidenze, dipendenze e stato epistemico; l'autorità di approvazione decide; l'autorità di pubblicazione esegue soltanto un atto umano esplicito. Autore e revisore sono separati quando possibile e devono esserlo per assessment approvati. Approvazione, rifiuto, supersessione e ritiro richiedono motivo, timestamp e identità. `review_due` è obbligatorio per record revisionabili.

Nuova evidenza, correzione materiale, dipendenza scoperta, fonte ritirata o contraddizione riaprono la revisione. Correzioni non materiali sono versionate; correzioni materiali generano una nuova versione con `supersedes`. La pubblicazione automatica è vietata; nessun record non `approved` può transitare a `published`.
