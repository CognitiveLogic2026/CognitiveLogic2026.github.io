# Piano separato di pubblicazione e integrazione

Stato: proposta non eseguita. International Watch resta separato dal core QEN Sovereign.

Una futura release potrebbe usare `/international-watch/` come indice e `/international-watch/cases/iw-001/` come dossier. La pagina caso dovrebbe mostrare disclaimer metodologico, cut-off/versione, stato di revisione, sintesi descrittiva degli stati, Claim/Evidence Matrix accessibile, grafo delle dipendenze, contraddizioni, cronologia, fonti e sezione «Cosa non sappiamo». Nessun punteggio o ranking.

L'eventuale Source Registry/Index QEN richiede mapping e approvazione separati: il registry IW non è allowlist QEN. Un retrieval futuro dovrebbe essere deterministico, limitato a record approvati e versionati, senza RAG, embeddings o modifiche al core in questa fase.

Versionamento: schemi SemVer; record immutabili dopo pubblicazione; correzioni materiali con `supersedes`; riesame almeno alla `review_due` e immediato per nuova evidenza, fonte ritirata o contraddizione. Rollback mediante ritiro della versione pubblica e ripristino dell'ultima versione approvata, conservando audit trail.

Test richiesti prima di qualunque esecuzione: rendering, accessibilità, collegamenti, noindex/staging, riferimenti, schema, sicurezza, privacy/copyright, rollback, sitemap separatamente autorizzata e non regressione. Rischi: perdita di qualificatori, fonte dinamica obsoleta, falsa indipendenza, esposizione prematura, divergenza tra JSON e pagina.

Gate: approvazione editoriale, legale/copyright, sicurezza, owner del registro, owner del sito, test staging, piano rollback e autorizzazione esplicita a commit/deploy. Nessuna azione di questo piano è autorizzata dalla Fase 3.
