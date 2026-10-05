from typing import Literal

from pydantic import BaseModel, Field


ActivityType = Literal[
    "balneare",
    "beach_club",
    "chiosco",
    "ambulante_food",
    "ambulante_nonfood",
    "mercato",
    "dehors",
]

CCNLType = Literal[
    "turismo",
    "commercio",
    "artigianato",
    "individuale",
    "nessuno",
]


class M1Input(BaseModel):
    concessione_regolare: bool
    bolkestein_ready: bool
    no_sanzioni: bool


class M2Input(BaseModel):
    plastica_kg: float = Field(..., ge=0)
    raccolta_differenziata_percentuale: float = Field(..., ge=0, le=100)
    bandiera_blu: bool
    no_plastica_monouso: bool
    pulizia_spiaggia: bool


class M3Input(BaseModel):
    bagnini: int = Field(0, ge=0)
    accessibile_balneare: bool = False
    defibrillatore: bool = False
    servizi_extra: bool = False

    anni_attivita: int = Field(0, ge=0)
    soddisfazione: float = Field(0, ge=0, le=5)
    accessibile_amb: bool = False
    prezzi_fissi: bool = False


class M4Input(BaseModel):
    fornitori_locali_percentuale: float = Field(..., ge=0, le=100)
    haccp: bool
    tracciabilita: bool
    bio: bool


class M5Input(BaseModel):
    ccnl: CCNLType
    formazione_ore: float = Field(..., ge=0)
    turnover_percentuale: float = Field(..., ge=0, le=100)
    alloggio: bool
    categorie_protette: bool


class M6Input(BaseModel):
    sito_web: bool
    social: bool
    recensioni: float = Field(..., ge=0, le=5)
    qr_code: bool


class BalneareAuditRequest(BaseModel):
    azienda_nome: str
    tipo: ActivityType
    m1: M1Input
    m2: M2Input
    m3: M3Input
    m4: M4Input
    m5: M5Input
    m6: M6Input


_AMB_TYPES = {
    "ambulante_food",
    "ambulante_nonfood",
    "mercato",
    "dehors",
}


def score_m1(d: M1Input) -> float:
    return min(
        (50 if d.concessione_regolare else 0)
        + (30 if d.bolkestein_ready else 0)
        + (20 if d.no_sanzioni else 0),
        100,
    )


def score_m2(d: M2Input) -> float:
    score = min(d.raccolta_differenziata_percentuale, 100)
    score -= min(d.plastica_kg * 4, 60)

    if d.raccolta_differenziata_percentuale >= 90:
        score += 10
    if d.bandiera_blu:
        score += 20
    if d.no_plastica_monouso:
        score += 10
    if d.pulizia_spiaggia:
        score += 10

    return max(0, min(score, 100))


def score_m3(tipo: ActivityType, d: M3Input) -> float:
    if tipo not in _AMB_TYPES:
        score = 0

        if d.bagnini >= 2:
            score += 25
        elif d.bagnini == 1:
            score += 10

        if d.accessibile_balneare:
            score += 30
        if d.defibrillatore:
            score += 15
        if d.servizi_extra:
            score += 10

        return min(score, 100)

    anni = min(d.anni_attivita, 6)

    score = min(anni * 5, 30)
    score += min(d.soddisfazione * 10, 50)

    if d.accessibile_amb:
        score += 20
    if d.prezzi_fissi:
        score += 10

    return min(score, 100)


def score_m4(d: M4Input) -> float:
    score = min(d.fornitori_locali_percentuale * 0.6, 60)

    if d.haccp:
        score += 30
    if d.tracciabilita:
        score += 10
    if d.bio:
        score += 10

    return min(score, 100)


def score_m5(d: M5Input) -> float:
    score = 0 if d.ccnl == "nessuno" else 50

    if d.formazione_ore > 40:
        score += 30
    elif d.formazione_ore > 20:
        score += 20
    elif d.formazione_ore > 0:
        score += 10

    if d.turnover_percentuale < 30:
        score += 15
    elif d.turnover_percentuale > 60:
        score -= 20

    if d.alloggio:
        score += 10
    if d.categorie_protette:
        score += 15

    return max(0, min(score, 100))


def score_m6(d: M6Input) -> float:
    score = 0

    if d.sito_web:
        score += 25
    if d.social:
        score += 20

    score += min(d.recensioni * 7, 35)

    if d.qr_code:
        score += 20

    return min(score, 100)


def compute_balneare_audit(req: BalneareAuditRequest) -> dict:
    scores = {
        "m1": score_m1(req.m1),
        "m2": score_m2(req.m2),
        "m3": score_m3(req.tipo, req.m3),
        "m4": score_m4(req.m4),
        "m5": score_m5(req.m5),
        "m6": score_m6(req.m6),
    }

    qen = round(
        scores["m1"] * 0.25
        + scores["m2"] * 0.20
        + scores["m3"] * 0.15
        + scores["m4"] * 0.15
        + scores["m5"] * 0.15
        + scores["m6"] * 0.10,
        1,
    )

    return {
        "azienda_nome": req.azienda_nome,
        "tipo": req.tipo,
        "scores": scores,
        "qen_score_finale": qen,
    }
