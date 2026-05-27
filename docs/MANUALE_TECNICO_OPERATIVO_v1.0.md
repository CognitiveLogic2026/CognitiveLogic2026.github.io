# MANUALE TECNICO OPERATIVO: MOTORE QEN v1.0

**Proprietà:** CognitiveLogic Intelligence  
**Autore:** Roberto Bob Malini  
**Data:** 20 Gennaio 2026  
**Versione:** 1.0  

## INTRODUZIONE

Il motore QEN (Quantificazione dell'Etica Naturale) è un algoritmo proprietario per il settore HoReCa. Funge da Filtro Deontologico per trasformare i flussi operativi in dati oggettivi, garantendo la conformità alla Direttiva Green Claim UE.

## DASHBOARD (3 PANNELLI)

1. Widget Compliance Legale (soglia minima 60%)
2. Registro Analitico Azioni Validate
3. Feed Intelligence Strategica

## I 10 PILASTRI (Pesi Totali 100%)

| Modulo | Peso | Obiettivo |
|--------|------|-----------|
| Logistica (Km-Zero) | 20% | Riduzione Scope 3 |
| Imballaggi (PPWR) | 20% | Economia Circolare |
| Risorse (Acqua/Energia) | 20% | Efficientamento Reale |
| Qualità/Biodiversità | 20% | Validazione Scientifica |
| Dignità Lavoro (ESG) | 10% | Responsabilità Sociale |
| Ciclo Rifiuti | 10% | Zero Waste |
| Trasparenza/Governance | 5% | Integrità Admin |
| Territorio | 5% | Valore Locale |
| Privacy Digitale | 5% | Sovranità Dati |
| Formazione Etica | 5% | Sviluppo Continuo |

## FORMULA MAESTRA

QEN Score = Σ (Modulo_i × Peso_i) [0-100]

**Soglia Conformità:** 60/100 = Green Claim Safe

## MODULO 1: LOGISTICA (20%)

**Input:** Km fornitore, tipo mezzo, certificazioni  
**Logica:**
- Distanza < 70km → Score 100
- Distanza > 70km → Decadimento (100 - dist/10)
- Bonus +20% se certificato
- **Compliance:** Blocca "Km-Zero" se < 80

## MODULO 2: IMBALLAGGI (20%)

**Input:** Plastica monouso, % riciclato, EN 13432  
**Logica:**
- -2 punti per kg plastica non necessaria
- +40 se riciclato > 30%
- +20 se biodegradabile certificato

## MODULO 3: RISORSE (20%)

**Input:** kWh, % rinnovabile, litri acqua, coperti  
**Logica:**
- Target 2 kWh/coperto
- Target 25 litri/coperto
- +30 se 100% rinnovabile

## MODULO 4: QUALITÀ (20%)

**Input:** Certificazioni ISO, indice biodiversità, stagionalità  
**Logica:**
- +5 punti per certificazione UE
- +10 per varietà rare/protette
- Moltiplicatore stagionale 1.0/0.5

## MODULO 5: SOCIALE (10%)

**Input:** Ore extra, gender gap, formazione, turnover  
**Logica:**
- Penalità se ore extra > 20%
- Penalità proporzionale al gender gap
- +20 se formazione etica > 40 ore/anno

## MODULO 6: RIFIUTI (10%)

**Input:** Scarto organico/pasto, % donato, oli, differenziata  
**Logica:**
- Bonus se scarto < 150g/cliente
- +30 per donazioni certificate
- Premia > 90% raccolta differenziata

## MODULO 7: TRASPARENZA (5%)

**Input:** QR Code data, audit esterni, codice etico, aggiornamenti  
**Logica:**
- +40 se dati pubblici per consumatore
- Bonus verifiche terzi
- Penalità se non aggiornato ogni 30gg

## MODULO 8: TERRITORIO (5%)

**Input:** % acquisti locali <50km, volontariato, inclusione, DE.CO  
**Logica:**
- +40 se > 60% budget territorio
- Bonus inserimento categorie protette
- Bonus biodiversità culturale

## MODULO 9: PRIVACY (5%)

**Input:** Data minimization, crittografia, dark patterns, audit IT  
**Logica:**
- +30 privacy by design
- +30 protocolli avanzati
- Punteggio consenso informato

## MODULO 10: FORMAZIONE (5%)

**Input:** Ore etica/anno, innovazioni sostenibili, sentiment clienti  
**Logica:**
- Target 20 ore formazione/anno
- Bonus nuove tecnologie basso impatto
- Integra percezione cliente

## SISTEMA

- **Soglia Conformità:** 60/100
- **Output:** Certificato Trasparenza + Filtro Deontologico
- **Stack:** FastAPI + Claude Sonnet 4.6 + JSON graphs
- **Deployment:** Hetzner CAX21 (port 8000)

## COMPLIANCE

- EU Green Claims Directive
- EU AI Act (Allegati I-III)
- GDPR Art. 22 + 35

## PILOT SCORES

- Veganoo: 79.0
- Colt Fragranza: 81.2
- Bologna100Botteghe: 79.5
- CNA Bologna Benchmark: 77.75

---

**Repository:** CognitiveLogic2026/CognitiveLogic2026.github.io  
**License:** © 2026 CognitiveLogic Intelligence
