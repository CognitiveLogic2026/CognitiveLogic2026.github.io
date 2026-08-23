from sovereign_engine import classify_risk, qen_score, score_entity


def test_qen_formula():
    assert qen_score(80, 70, 60) == 71.5


def test_qen_normalizes_scale():
    assert qen_score(8, 7, 6) == 71.5


def test_high_risk_classification():
    result = classify_risk(
        "Sistema biometrico per la selezione automatizzata del personale"
    )
    assert result["risk_level"] == "HIGH"
    assert result["gdpr_risk"] == "HIGH"
    assert result["engine"] == "QEN Sovereign Intelligence Engine"


def test_low_risk_classification():
    result = classify_risk("Sistema per ottimizzare il consumo energetico")
    assert result["risk_level"] == "LOW"


def test_explicit_entity_score():
    result = score_entity(
        "Impresa Test",
        "Audit documentato",
        "HoReCa",
        vs=80,
        va=70,
        vt=60,
    )
    assert result["qen_score"] == 71.5
    assert result["provider"] == "qen-sovereign"
