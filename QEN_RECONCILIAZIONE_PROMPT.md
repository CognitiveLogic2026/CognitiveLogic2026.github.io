# QEN Riconciliazione — Prompt di Sistema

<!-- Copyright (c) 2026 Roberto Bob Malini - Cognitive Logic -->
<!-- https://www.cognitivelogic.it -->
<!-- Licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/) -->

## Scopo

Questo documento descrive il prompt di sistema e la metodologia operativa del motore di **riconciliazione QEN** (Quantification of Ethical Naturalness). Il motore confronta i dati autodichiarati dagli operatori con fonti esterne certificate, calcola scostamenti e aggiorna il punteggio QEN in modo automatico e tracciabile.

---

## Prompt di Riconciliazione (template LLM)

```
Sei il motore di riconciliazione QEN di Cognitive Logic.

Il tuo compito è analizzare i parametri autodichiarati da un operatore economico e
confrontarli con i valori verificati da fonti esterne certificate.

### Operatore
- ID: {operator_id}
- Nome: {operator_name}

### Parametri dichiarati
{declared_data_json}

### Valori verificati da fonti esterne
{verified_data_json}

### Istruzioni

Per ciascun parametro:
1. Calcola lo scostamento percentuale tra dichiarato e verificato.
2. Assegna uno stato secondo la soglia:
   - ALIGNED  → scostamento = 0%
   - GREEN    → scostamento ≤ 15%
   - YELLOW   → scostamento ≤ 30%
   - RED      → scostamento > 30%  (o disallineamento booleano)
3. Applica l'aggiustamento al punteggio base:
   - ALIGNED  →   0 punti
   - GREEN    →  −5 punti
   - YELLOW   → −15 punti
   - RED      → −30 punti
4. Per stati RED e YELLOW apri automaticamente un'escalation verso il supervisore.

### Output atteso (JSON)

{
  "reconciliation_id": "REC_XXXXXXXX",
  "operator_id": "{operator_id}",
  "operator_name": "{operator_name}",
  "parameter_results": [
    {
      "parameter": "<nome_parametro>",
      "declared": <valore_dichiarato>,
      "verified": <valore_verificato>,
      "source": "<fonte_esterna>",
      "reliability": <0.0-1.0>,
      "discrepancy_pct": <0.0-100.0>,
      "status": "ALIGNED|GREEN|YELLOW|RED",
      "adjustment": <0|-5|-15|-30>,
      "message": "<messaggio_leggibile>"
    }
  ],
  "qen_score": {
    "before": <punteggio_base>,
    "after": <punteggio_rettificato>,
    "adjustment": <somma_aggiustamenti>
  },
  "timestamp": "<ISO8601>"
}

Restituisci esclusivamente il JSON. Nessun testo aggiuntivo.
```

---

## Parametri Riconciliabili

| Parametro | Fonte esterna | Affidabilità | Tipo |
|---|---|---|---|
| `distanza_media_fornitori_km` | OpenStreetMap | 0.75 | Numerico |
| `biologico_certificato` | ICEA | 0.90 | Booleano |
| `percentuale_scarti` | InfoCamere | 0.75 | Numerico |
| `consumo_kwh_anno` | InfoCamere | 0.75 | Numerico |
| `eu_ai_compliant` | NANDO | 0.92 | Booleano |

I parametri non presenti in questa tabella vengono considerati `ALIGNED` (nessuna fonte disponibile) e non generano aggiustamenti né escalation.

---

## Logica di Scostamento

### Parametri numerici

```
scostamento = |dichiarato − verificato| / |verificato|
```

Se `verificato = 0`, lo scostamento è `0.0` (nessun riferimento disponibile).

### Parametri booleani

```
scostamento = 0.0  se  dichiarato == verificato
scostamento = 1.0  se  dichiarato != verificato
```

Un disallineamento booleano produce sempre stato `RED`.

---

## Soglie e Aggiustamenti

```
ALIGNED  scostamento = 0.00                  →  +0 pt
GREEN    0.00 < scostamento ≤ 0.15           →  −5 pt
YELLOW   0.15 < scostamento ≤ 0.30           → −15 pt
RED      scostamento > 0.30  (o bool mismatch) → −30 pt
```

Il punteggio QEN finale non scende mai sotto `0`.

---

## Punteggio Base e Composizione QEN

Il punteggio di partenza prima della riconciliazione è **75/100** (default).

La riconciliazione si applica **sopra** al punteggio già calcolato dal modello di scoring primario (Bolkestein pipeline):

| Dimensione | Peso | Descrizione |
|---|---|---|
| VS — Valore Sociale | 0.35 | Certificazioni, CCNL, HR |
| VA — Valore Ambientale | 0.35 | Energia, rifiuti, certificazioni ambientali |
| VT — Valore Territoriale | 0.30 | Filiera locale, prossimità fornitori |

```
QEN_raw   = 0.35 × VS + 0.35 × VA + 0.30 × VT
QEN_final = max(0, QEN_raw + Σ aggiustamenti_riconciliazione)
```

---

## Workflow Escalation

```
Parametro riconciliato
        │
        ├─ ALIGNED / GREEN ──► nessuna azione
        │
        └─ YELLOW / RED ──► Escalation OPEN
                                │
                          Supervisore riceve notifica
                                │
                    POST /api/escalations/{esc_id}/resolve
                         Header: X-Supervisor-Key
                                │
                          Escalation RESOLVED
                         (resolved_by, resolution_notes, resolved_at)
```

### Struttura record escalation

```json
{
  "id": "ESC_XXXXXXXX",
  "reconciliation_id": "REC_XXXXXXXX",
  "operator_id": "op_001",
  "operator_name": "Bottega Contadina",
  "parameter": "biologico_certificato",
  "declared": true,
  "verified": false,
  "source": "ICEA",
  "discrepancy_pct": 100.0,
  "status": "RED",
  "escalation_status": "OPEN",
  "resolved_at": null,
  "resolved_by": null,
  "resolution_notes": null,
  "timestamp": "2026-05-27T10:00:00Z"
}
```

---

## Endpoints API

| Metodo | Path | Descrizione |
|---|---|---|
| `GET` | `/health` | Stato del servizio e configurazione chiavi |
| `POST` | `/api/ingest` | Acquisizione dati dichiarati (senza scoring) |
| `POST` | `/api/reconcile` | Riconciliazione completa + aggiornamento score |
| `GET` | `/api/escalations` | Lista escalation (filtro: `?status=OPEN\|RESOLVED`) |
| `POST` | `/api/escalations/{esc_id}/resolve` | Risoluzione escalation (supervisore) |

### Esempio chiamata riconciliazione

```bash
curl -X POST https://api.cognitivelogic.it/api/reconcile \
  -H "Content-Type: application/json" \
  -d '{
    "operator_id": "op_001",
    "operator_name": "Bottega Contadina",
    "base_score": 75,
    "declared_data": {
      "distanza_media_fornitori_km": 80,
      "biologico_certificato": true,
      "percentuale_scarti": 9.0,
      "consumo_kwh_anno": 42000,
      "eu_ai_compliant": true
    }
  }'
```

---

## Fonti Esterne — Note di Integrazione

| Fonte | Variabile env | Fallback |
|---|---|---|
| ICEA (certificazione biologica) | `ICEA_API_KEY` | Mock → `true` |
| InfoCamere (registri imprese) | `INFOCAMERE_API_KEY` | Mock → valori tipici di settore |
| OpenStreetMap | — | Valore statico `115.0 km` |
| NANDO (EU AI Act) | — | Mock → `true` |

In assenza delle chiavi API, il sistema utilizza valori mock per garantire la continuità operativa. Impostare le variabili d'ambiente sul server di produzione per attivare le chiamate reali.

---

## Garanzie di Audit

Ogni riconciliazione produce:
- un `reconciliation_id` univoco (`REC_` + hash MD5 troncato)
- timestamp ISO 8601 in UTC
- traccia completa: dichiarato, verificato, fonte, affidabilità, scostamento, stato, aggiustamento

I record di escalation sono persistiti in `/app/cognitivelogic/escalations.json` e non vengono mai cancellati automaticamente.

---

*Cognitive Logic — QEN Framework v2.0 — Roberto Bob Malini*
*CC BY-SA 4.0 — https://cognitivelogic.it*
