# Validation Status — CognitiveLogic QEN Platform

Ultimo aggiornamento: 2026-05-31

Questo file documenta le dipendenze esterne, lo stato di attivazione e
il comportamento di fallback (mock/stub) quando le chiavi API non sono
configurate.

---

## Dipendenze API esterne

### ICEA_API_KEY

| Campo | Valore |
|-------|--------|
| Stato | **stub** |
| Secret GitHub | `ICEA_API_KEY` |
| Comportamento senza chiave | `biologico_certificato` restituisce `True` (mock statico) |
| Endpoint reale | `https://api.icea.bio/v1/certification` (da attivare) |

Quando `ICEA_API_KEY` non è impostata, la funzione `_fetch_icea()` in
`qen-reconciliation/main.py` restituisce dati simulati. I punteggi QEN
che dipendono dalla certificazione biologica sono quindi approssimativi.

---

### INFOCAMERE_API_KEY

| Campo | Valore |
|-------|--------|
| Stato | **stub** |
| Secret GitHub | `INFOCAMERE_API_KEY` |
| Comportamento senza chiave | `percentuale_scarti` e `consumo_kwh` sono valori mock |
| Endpoint reale | InfoCamere RI/Integra (da attivare) |

Quando `INFOCAMERE_API_KEY` non è impostata, i dati provenienti dal
Registro delle Imprese (scarti di produzione, consumi energetici) sono
simulati. Le analisi di riconciliazione restituiscono comunque un
risultato, ma con dati non verificati da fonte ufficiale.

---

### OpenAI (OPENAI_API_KEY)

| Campo | Valore |
|-------|--------|
| Stato | **disabilitato** |
| Motivo | Pagamento in sospeso — credito OpenAI esaurito |
| Endpoint | `POST /agents/openai-advisor` |
| Risposta attuale | `503 endpoint_disabled` |
| Alternativa | `POST /agents/mistral-advisor` (Mistral AI, operativo) |

L'endpoint `/agents/openai-advisor` è registrato nel router di
`orchestrator.py` ma risponde sempre con `503`. Non effettua chiamate
a `api.openai.com`. Il modello `gpt-4o-mini` può essere riabilitato
impostando `OPENAI_API_KEY` e ripristinando il corpo della funzione
`openai_advisor()`.

---

## Moduli non in produzione

### qen-bolkestein/

| Campo | Valore |
|-------|--------|
| Stato | **locale — non deployato in produzione** |
| Path | `qen-bolkestein/` |
| Scopo | Scoring normativo Direttiva Bolkestein per operatori HoReCa |
| Utilizzo | Sviluppo/test locale; non esposto via nginx su `api.cognitivelogic.it` |

Il modulo `qen-bolkestein/` è presente nel repository ma non è incluso
nei service unit systemd né nel routing nginx. Viene usato localmente
tramite `qen_bolkestein_s4.py` per sviluppo e validazione del modello.

---

## Servizi operativi

| Servizio | Porta | Stato |
|----------|-------|-------|
| Flask QEN API | 5000 | Operativo |
| FastAPI QEN Reconciliation | 8001 | Operativo |
| Nginx reverse proxy | 443 | Operativo |
| Orchestrator (Claude + Gemini) | — | Operativo |
| Mistral advisor | — | Operativo |
| OpenAI advisor | — | Disabilitato (503) |
| qen-bolkestein | — | Solo locale |

---

## Rate Limiting (Flask-Limiter 4.1)

| Campo | Valore |
|-------|--------|
| Storage | In-memory (`memory://`) |
| Limite endpoint LLM singolo | 30 req/min per IP |
| Limite endpoint batch LLM | 20 req/min per IP |
| Nota multi-worker | Gunicorn avvia `--workers 2`: ogni worker ha il proprio contatore separato. Il limite effettivo per IP è fino a **2× quello configurato** (es. 60 invece di 30/min). Per un VPS B2B a traffico controllato è accettabile. Soluzione definitiva: configurare Redis come storage backend (`RATELIMIT_STORAGE_URI=redis://localhost:6379`). |
