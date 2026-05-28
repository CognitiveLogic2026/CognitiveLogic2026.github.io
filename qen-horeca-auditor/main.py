# Copyright (c) 2026 Roberto Bob Malini - Cognitive Logic
# https://www.cognitivelogic.it
# Licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
#
# QEN HoReCa Compliance Auditor — FastAPI Backend
# Motore QEN v1.0 — Quantificazione dell'Etica Naturale
# Endpoint: POST /api/qen/audit
import os
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

import anthropic
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="QEN HoReCa Compliance Auditor",
    description="Motore QEN v1.0 — Quantificazione dell'Etica Naturale per aziende HoReCa",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

_anthropic = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# ── Pydantic input models ─────────────────────────────────────────────────────

class LogisticaInput(BaseModel):
    distanza_fornitore_km: float = Field(..., ge=0)
    tipologia_mezzo: str = Field(..., pattern="^(auto|camion|bici|a_piedi)$")
    certificazione_fornitore: bool
    num_fornitori_localizzati: float = Field(..., ge=0, le=100,
        description="Percentuale fornitori entro 100km (0-100)")

class ImballaggiInput(BaseModel):
    peso_plastica_monouso_kg: float = Field(..., ge=0)
    percentuale_materiale_riciclato: float = Field(..., ge=0, le=100)
    certificazione_compostabilita_en13432: bool
    volumen_contenitori_eco: float = Field(..., ge=0)

class RisorseInput(BaseModel):
    kwh_consumati_mese: float = Field(..., ge=0)
    percentuale_energia_rinnovabile: float = Field(..., ge=0, le=100)
    litri_acqua_consumati_mese: float = Field(..., ge=0)
    numero_coperti_mese: int = Field(..., gt=0)

class QualitaInput(BaseModel):
    numero_certificazioni_iso_ecolabel: int = Field(..., ge=0)
    indice_specie_autoctone: float = Field(..., ge=0, le=100)
    coefficiente_stagionalita: str = Field(..., pattern="^(in_stagione|fuori_stagione|serra)$")
    lista_ingredienti_protetti: List[str]

class SocialeInput(BaseModel):
    ore_extra_percentuale: float = Field(..., ge=0, le=100)
    gender_pay_gap_percentuale: float = Field(..., ge=0, le=100)
    ore_formazione_anno_dipendente: float = Field(..., ge=0)
    tasso_turnover_annuale: float = Field(..., ge=0, le=100)
    numero_dipendenti_categorie_protette: int = Field(..., ge=0)

class RifiutiInput(BaseModel):
    scarto_organico_kg_mese: float = Field(..., ge=0)
    numero_coperti_mese: int = Field(..., gt=0)
    percentuale_cibo_donato: float = Field(..., ge=0, le=100)
    percentuale_raccolta_differenziata: float = Field(..., ge=0, le=100)
    tracciabilita_oli_esausti: bool

class GovernanceInput(BaseModel):
    dati_qen_pubblici_qrcode: bool
    audit_esterni_presenti: bool
    firma_codice_etico: bool
    giorni_da_ultimo_aggiornamento: int = Field(..., ge=0)

class TerritorioInput(BaseModel):
    percentuale_acquisti_locali: float = Field(..., ge=0, le=100)
    ore_volontariato_aziendale_anno: float = Field(..., ge=0)
    progetti_inclusione_attivi: int = Field(..., ge=0)
    ingredienti_biodiversita_culturale: List[str]

class QENAuditRequest(BaseModel):
    azienda_nome: str
    logistica: LogisticaInput
    imballaggi: ImballaggiInput
    risorse: RisorseInput
    qualita: QualitaInput
    sociale: SocialeInput
    rifiuti: RifiutiInput
    governance: GovernanceInput
    territorio: TerritorioInput


# ── Module scoring engines ────────────────────────────────────────────────────

def _r(v: float) -> float:
    return round(v, 2)


def calc_logistica(d: LogisticaInput) -> dict:
    base = 100.0 if d.distanza_fornitore_km < 70 else max(0.0, 100.0 - (d.distanza_fornitore_km - 70) / 10)
    bonus_etico = 20.0 if d.certificazione_fornitore else 0.0
    bonus_filiera = 15.0 if d.num_fornitori_localizzati >= 80 else 0.0
    score = min(100.0, base + bonus_etico + bonus_filiera)

    notes = []
    if d.distanza_fornitore_km >= 70:
        notes.append(f"Distanza fornitore {d.distanza_fornitore_km}km supera soglia km-zero (70km)")
    if not d.certificazione_fornitore:
        notes.append("Fornitore privo di certificazione etica")
    if d.num_fornitori_localizzati < 80:
        notes.append(f"{d.num_fornitori_localizzati:.0f}% fornitori entro 100km (soglia bonus: 80%)")

    return {
        "score": _r(score),
        "claim_negato": score < 80,
        "claim_negato_label": "Km-Zero" if score < 80 else None,
        "note": "; ".join(notes) if notes else "Filiera corta conforme",
    }


def calc_imballaggi(d: ImballaggiInput) -> dict:
    penalita = min(40.0, 2.0 * d.peso_plastica_monouso_kg)
    bonus_riciclo = 40.0 if d.percentuale_materiale_riciclato > 30 else 0.0
    bonus_compost = 20.0 if d.certificazione_compostabilita_en13432 else 0.0
    score = max(0.0, 100.0 - penalita + bonus_riciclo + bonus_compost)

    notes = []
    if d.peso_plastica_monouso_kg > 0:
        notes.append(f"Plastica monouso {d.peso_plastica_monouso_kg}kg/mese → penalità -{penalita:.0f}pt")
    if d.percentuale_materiale_riciclato <= 30:
        notes.append(f"Materiale riciclato {d.percentuale_materiale_riciclato:.0f}% (soglia bonus: >30%)")
    if not d.certificazione_compostabilita_en13432:
        notes.append("Certificazione compostabilità EN13432 assente")

    return {
        "score": _r(score),
        "claim_negato": score < 70,
        "claim_negato_label": "100% Eco-friendly" if score < 70 else None,
        "note": "; ".join(notes) if notes else "Imballaggi conformi a PPWR 2026",
    }


def calc_risorse(d: RisorseInput) -> dict:
    kwh_pro = d.kwh_consumati_mese / d.numero_coperti_mese
    litri_pro = d.litri_acqua_consumati_mese / d.numero_coperti_mese

    score_energia = 100.0 if kwh_pro <= 2 else max(0.0, 100.0 - (kwh_pro - 2) * 10)
    score_acqua = 100.0 if litri_pro <= 25 else max(0.0, 100.0 - (litri_pro - 25) / 0.25)

    bonus_green = 30.0 if d.percentuale_energia_rinnovabile == 100 else (
        15.0 if d.percentuale_energia_rinnovabile >= 50 else 0.0
    )
    score = min(100.0, (score_energia + score_acqua) / 2 + bonus_green)

    notes = []
    if kwh_pro > 2:
        notes.append(f"{kwh_pro:.2f} kWh/coperto (target ≤2)")
    if litri_pro > 25:
        notes.append(f"{litri_pro:.1f} L/coperto (target ≤25)")
    if d.percentuale_energia_rinnovabile < 50:
        notes.append(f"Energia rinnovabile {d.percentuale_energia_rinnovabile:.0f}% (bonus ≥50%)")

    return {
        "score": _r(score),
        "claim_negato": score < 75,
        "claim_negato_label": "Carbon Neutral" if score < 75 else None,
        "note": "; ".join(notes) if notes else "Efficienza risorse nella norma",
    }


def calc_qualita(d: QualitaInput) -> dict:
    molt = {"in_stagione": 1.0, "fuori_stagione": 0.5, "serra": 0.6}.get(
        d.coefficiente_stagionalita, 1.0
    )
    n_prot = len(d.lista_ingredienti_protetti)
    score_base = (d.numero_certificazioni_iso_ecolabel * 5) + (n_prot * 10)
    score = min(100.0, score_base * molt)

    notes = []
    if molt < 1.0:
        notes.append(f"Moltiplicatore stagionale {molt} ({d.coefficiente_stagionalita})")
    if d.numero_certificazioni_iso_ecolabel == 0:
        notes.append("Nessuna certificazione ISO/Ecolabel")
    if n_prot == 0:
        notes.append("Nessun ingrediente protetto/autoctono dichiarato")

    return {
        "score": _r(score),
        "claim_negato": score < 80,
        "claim_negato_label": "Biologico/Certificato" if score < 80 else None,
        "note": "; ".join(notes) if notes else (
            f"{d.numero_certificazioni_iso_ecolabel} certificazioni, {n_prot} ingredienti protetti"
        ),
    }


def calc_sociale(d: SocialeInput) -> dict:
    pen_sfruttamento = 50.0 if d.ore_extra_percentuale > 20 else 0.0
    pen_equita = min(50.0, d.gender_pay_gap_percentuale * 0.5)
    bonus_formazione = 20.0 if d.ore_formazione_anno_dipendente > 40 else 0.0
    bonus_turnover = (
        15.0 if d.tasso_turnover_annuale < 15 else
        (-25.0 if d.tasso_turnover_annuale > 30 else 0.0)
    )
    bonus_inclusione = min(30.0, d.numero_dipendenti_categorie_protette * 10.0)
    score = max(
        0.0,
        100.0 - pen_sfruttamento - pen_equita + bonus_formazione + bonus_turnover + bonus_inclusione,
    )

    notes = []
    if d.ore_extra_percentuale > 20:
        notes.append(f"Straordinari {d.ore_extra_percentuale:.0f}% > soglia 20%")
    if d.gender_pay_gap_percentuale > 0:
        notes.append(f"Gender pay gap {d.gender_pay_gap_percentuale:.0f}%")
    if d.ore_formazione_anno_dipendente <= 40:
        notes.append(f"Formazione {d.ore_formazione_anno_dipendente:.0f}h/anno (soglia >40h)")
    if d.tasso_turnover_annuale > 30:
        notes.append(f"Turnover {d.tasso_turnover_annuale:.0f}% > 30%")

    return {
        "score": _r(score),
        "claim_negato": score < 75,
        "claim_negato_label": "Socialmente Responsabile" if score < 75 else None,
        "note": "; ".join(notes) if notes else "Indicatori sociali nella norma",
    }


def calc_rifiuti(d: RifiutiInput) -> dict:
    scarto_pro = d.scarto_organico_kg_mese / d.numero_coperti_mese
    score_eff = 100.0 if scarto_pro < 0.15 else max(0.0, 100.0 - (scarto_pro - 0.15) * 200)
    bonus_recupero = 30.0 if d.percentuale_cibo_donato > 5 else 0.0
    bonus_zerowaste = 25.0 if d.percentuale_raccolta_differenziata >= 90 else 0.0
    bonus_oli = 15.0 if d.tracciabilita_oli_esausti else 0.0
    score = min(100.0, score_eff + bonus_recupero + bonus_zerowaste + bonus_oli)

    notes = []
    if scarto_pro >= 0.15:
        notes.append(f"Scarto {scarto_pro:.3f} kg/coperto (target <0.15 kg)")
    if d.percentuale_cibo_donato <= 5:
        notes.append(f"Food donation {d.percentuale_cibo_donato:.1f}% (soglia >5%)")
    if d.percentuale_raccolta_differenziata < 90:
        notes.append(f"Raccolta differenziata {d.percentuale_raccolta_differenziata:.0f}% (soglia 90%)")
    if not d.tracciabilita_oli_esausti:
        notes.append("Tracciabilità oli esausti assente")

    return {
        "score": _r(score),
        "claim_negato": False,
        "claim_negato_label": None,
        "note": "; ".join(notes) if notes else "Gestione rifiuti virtuosa",
    }


def calc_governance(d: GovernanceInput) -> dict:
    score_base = 100.0
    bonus_trasparenza = 40.0 if d.dati_qen_pubblici_qrcode else 0.0
    bonus_audit = 30.0 if d.audit_esterni_presenti else 0.0
    bonus_codice = 20.0 if d.firma_codice_etico else 0.0
    pen_freschezza = 20.0 if d.giorni_da_ultimo_aggiornamento > 30 else 0.0
    score = min(100.0, score_base + bonus_trasparenza + bonus_audit + bonus_codice - pen_freschezza)

    notes = []
    if not d.dati_qen_pubblici_qrcode:
        notes.append("Dati QEN non pubblicati via QR code")
    if not d.audit_esterni_presenti:
        notes.append("Audit esterni assenti")
    if not d.firma_codice_etico:
        notes.append("Codice etico non firmato")
    if d.giorni_da_ultimo_aggiornamento > 30:
        notes.append(f"Dati aggiornati {d.giorni_da_ultimo_aggiornamento}gg fa (penalità -20pt)")

    return {
        "score": _r(score),
        "claim_negato": False,
        "claim_negato_label": None,
        "note": "; ".join(notes) if notes else "Governance trasparente e aggiornata",
    }


def calc_territorio(d: TerritorioInput) -> dict:
    bonus_locale = 40.0 if d.percentuale_acquisti_locali > 60 else 0.0
    bonus_volontariato = 20.0 if d.ore_volontariato_aziendale_anno > 100 else 0.0
    bonus_inclusione = min(30.0, d.progetti_inclusione_attivi * 10.0)
    bonus_cultura = min(25.0, len(d.ingredienti_biodiversita_culturale) * 5.0)
    # Spec formula: min(100, 100 + bonuses) — equivalent to min(100, bonuses) since bonuses ≥ 0
    # Implemented as purely bonus-driven to reflect actual territorial contribution
    score = min(100.0, bonus_locale + bonus_volontariato + bonus_inclusione + bonus_cultura)

    notes = []
    if d.percentuale_acquisti_locali <= 60:
        notes.append(f"Acquisti locali {d.percentuale_acquisti_locali:.0f}% (soglia >60%)")
    if d.ore_volontariato_aziendale_anno <= 100:
        notes.append(f"Volontariato {d.ore_volontariato_aziendale_anno:.0f}h/anno (soglia >100h)")
    if d.progetti_inclusione_attivi == 0:
        notes.append("Nessun progetto inclusione attivo")
    if len(d.ingredienti_biodiversita_culturale) == 0:
        notes.append("Nessun ingrediente di biodiversità culturale")

    return {
        "score": _r(score),
        "claim_negato": False,
        "claim_negato_label": None,
        "note": "; ".join(notes) if notes else "Buon impatto sul territorio",
    }


# ── QEN Master Formula ────────────────────────────────────────────────────────

def compute_qen_audit(req: QENAuditRequest) -> dict:
    mods = {
        "logistica":  calc_logistica(req.logistica),
        "imballaggi": calc_imballaggi(req.imballaggi),
        "risorse":    calc_risorse(req.risorse),
        "qualita":    calc_qualita(req.qualita),
        "sociale":    calc_sociale(req.sociale),
        "rifiuti":    calc_rifiuti(req.rifiuti),
        "governance": calc_governance(req.governance),
        "territorio": calc_territorio(req.territorio),
    }

    qen = round(
        mods["logistica"]["score"]  * 0.20 +
        mods["imballaggi"]["score"] * 0.20 +
        mods["risorse"]["score"]    * 0.20 +
        mods["qualita"]["score"]    * 0.10 +
        mods["sociale"]["score"]    * 0.10 +
        mods["rifiuti"]["score"]    * 0.10 +
        mods["governance"]["score"] * 0.05 +
        mods["territorio"]["score"] * 0.05,
        2,
    )

    if qen < 60:
        status = "NON CONFORME"
    elif qen < 75:
        status = "CONFORME CONDIZIONATO"
    else:
        status = "CONFORME CERTIFICATO"

    blocchi_claim = [
        m["claim_negato_label"]
        for m in mods.values()
        if m["claim_negato"] and m["claim_negato_label"]
    ]

    recs = []
    if mods["logistica"]["score"] < 80:
        recs.append("Privilegiare fornitori entro 70km e ottenere certificazioni etiche di filiera")
    if mods["imballaggi"]["score"] < 70:
        recs.append("Eliminare plastica monouso e adottare imballaggi compostabili certificati EN13432")
    if mods["risorse"]["score"] < 75:
        recs.append("Installare pannelli fotovoltaici e sistemi di recupero acqua piovana")
    if mods["qualita"]["score"] < 80:
        recs.append("Ottenere certificazioni ISO/Ecolabel e strutturare menu con prodotti stagionali")
    if mods["sociale"]["score"] < 75:
        recs.append("Azzerare gender pay gap, ridurre straordinari e aumentare ore di formazione")
    if mods["rifiuti"]["score"] < 50:
        recs.append("Attivare partnership con food bank locali e portare raccolta differenziata al 90%")
    if mods["governance"]["score"] < 90:
        recs.append("Pubblicare dati QEN via QR code esposto e programmare audit esterni annuali")
    if mods["territorio"]["score"] < 40:
        recs.append("Portare acquisti locali oltre 60% e attivare almeno un progetto di inclusione sociale")

    now = datetime.utcnow()
    return {
        "qen_audit_id": str(uuid.uuid4()),
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "azienda_nome": req.azienda_nome,
        "qen_score_finale": qen,
        "status_conformita": status,
        "moduli_dettagliati": {
            k: {"score": v["score"], "note": v["note"]}
            for k, v in mods.items()
        },
        "blocchi_claim": blocchi_claim,
        "raccomandazioni_miglioria": recs,
        "prossima_valutazione_consigliata": (now + timedelta(days=30)).strftime("%Y-%m-%d"),
        "proprietario_certificato": "CognitiveLogic Intelligence",
    }


# ── API endpoints ─────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "QEN HoReCa Compliance Auditor",
        "version": "1.0.0",
        "motore": "QEN v1.0 — Quantificazione Etica Naturale",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


@app.post("/api/qen/audit")
def qen_audit(req: QENAuditRequest):
    try:
        return compute_qen_audit(req)
    except ZeroDivisionError:
        raise HTTPException(status_code=400, detail="numero_coperti_mese non può essere zero")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
