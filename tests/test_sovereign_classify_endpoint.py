import os
from unittest.mock import patch

os.environ["COGNITIVE_API_KEY"] = "test-key-ci"

from main import app

client = app.test_client()
HEADERS = {"X-API-Key": "test-key-ci"}


def test_classify_risk_requires_description():
    response = client.post(
        "/classify-risk",
        json={},
        headers=HEADERS,
    )

    assert response.status_code == 400


def test_classify_risk_uses_sovereign_engine_without_anthropic():
    with patch(
        "main.get_anthropic_client",
        side_effect=AssertionError("Anthropic must not be called"),
    ):
        response = client.post(
            "/classify-risk",
            json={
                "descrizione": (
                    "Sistema biometrico per la selezione automatizzata "
                    "del personale"
                ),
                "contesto": "Assunzioni",
                "settore": "Risorse umane",
            },
            headers=HEADERS,
        )

    assert response.status_code == 200

    payload = response.get_json()
    assert isinstance(payload, dict)
    assert payload["status"] == "success"
    assert payload["sistema"]

    classification = payload["classificazione"]
    assert classification["livello_rischio"]
    assert classification["motivazione"]
    assert "qen_impact" in classification
    assert "vs" in classification
    assert "va" in classification
    assert "vt" in classification
