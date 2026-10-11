# Pilot balneari — acquisizione tramite evidenze
Data: 11 ottobre 2026. Responsabile: Roberto Malini.

## Decisione
Sospesa la strategia di banca dati e outreach indiscriminato a 1.000 concessionari. L'ingresso commerciale è l'Audit Preliminare della Concessione Demaniale, inizialmente gratuito e basato su fonti pubbliche. Nessuna promessa sull'esito della gara.

## Verifica del percorso esistente
- /balneari-assessment/: HTTP 404 al controllo del 11 ottobre.
- /_preview/balneari-assessment/: HTTP 401 senza credenziali, corretta protezione. Contenuto autenticato non verificato.
- Branch feature/balneari-commercial-assessment-20261010: non reperito tra i branch remoti cercati. Potrebbe essere rimasto sul VPS; non ricostruire il prodotto senza aver controllato quella copia.
- qen-balneare-auditor.html: presente in main. Calcolo deterministico e dichiarazioni su certificazione, conformità e scadenze richiedono revisione prima dell'impiego commerciale. Non collegato nel nuovo percorso.
- Osservatorio e analisi Rimini: riutilizzati senza cambiare evidenze, pesi o conclusioni normative.

## Percorso implementato
Analisi Rimini o guida prima del bando -> Osservatorio #verifica-preliminare -> Comune, stabilimento, situazione, email e privacy -> composizione di email -> invio volontario dal client.
Fallback: testo della richiesta copiabile e indirizzo email visibile. Nessun database prospect, salvataggio nel browser o invio automatico. La preparazione del testo non dimostra un invio né una richiesta ricevuta.

## Tre territori iniziali
- Rimini: analisi esistente collegata all'ingresso commerciale. Prima di un nuovo rilancio aggiornare gli atti/esiti comunali; l'articolo ha cut-off 27 settembre.
- Cervia: acquisire uno specifico atto primario e verificarne la portata prima di pubblicare una nuova scheda. Il riferimento AS2164 nell'Osservatorio non basta per inferire lo stato di una gara.
- Cesenatico: acquisire uno specifico atto primario prima di pubblicare una nuova scheda. Nessun bando o rischio specifico è attestato da questa modifica.

## Misurazione per 30 giorni dalla pubblicazione
La provenienza (Analisi Rimini, Guida prima del bando, Osservatorio) è inclusa nel testo dell'email. Registrare solo richieste realmente ricevute in info@cognitivelogic.it.
Richiesta qualificata: Comune e stabilimento identificabili, problema pertinente e contatto utilizzabile; duplicati dello stesso caso contano una volta.
Obiettivo sperimentale: 3–5 richieste qualificate; non è una previsione.
Visite, clic e assessment completati NON vengono misurati da questa modifica: occorre verificare la strumentazione disponibile prima di riportare conversioni. L'email può essere modificata dal mittente e la provenienza è un'indicazione, non una prova di attribuzione.
Per ogni richiesta: data, territorio, fonte dichiarata, problema, fonti reperibili, lacune, prossimo passo, stato risposta. Conservare i dati nei sistemi privati destinati alle richieste, mai nel repository pubblico.

## Passi ancora necessari
1. Recuperare e verificare la copia locale dell'assessment balneare sul VPS e la preview autenticata.
2. Validare il primo controllo su una richiesta effettiva.
3. Verificare fonti primarie di Cervia e Cesenatico.
4. Controllare analytics disponibili e registrare soltanto metriche osservabili.
5. Esaminare i risultati dopo 30 giorni; nessun outreach massivo da riattivare automaticamente.
