from unittest.mock import patch

from main import app


def _headers(response):
    return {key.lower(): value for key, value in response.headers.items()}


def test_gemini_qen_score_has_deprecation_headers():
    client = app.test_client()

    with patch("main._require_trusted_origin", return_value=None):
        response = client.post(
            "/gemini/qen-score",
            json={
                "business_name": "Test",
                "sector": "horeca",
                "description": "Attività di test",
            },
        )

    headers = _headers(response)

    assert headers["deprecation"] == "true"
    assert headers["x-qen-compatibility-route"] == "legacy-gemini"
    assert '</copilot-analyze>; rel="successor-version"' in headers["link"]


def test_gemini_compliance_error_has_deprecation_headers():
    client = app.test_client()

    with patch("main._require_trusted_origin", return_value=None):
        response = client.post(
            "/gemini/compliance-audit",
            json={"system_name": "Test"},
        )

    assert response.status_code == 400

    headers = _headers(response)

    assert headers["deprecation"] == "true"
    assert headers["x-qen-compatibility-route"] == "legacy-gemini"
    assert '</copilot-analyze>; rel="successor-version"' in headers["link"]


def test_non_gemini_route_has_no_legacy_header():
    client = app.test_client()
    response = client.get("/health")

    headers = _headers(response)

    assert "x-qen-compatibility-route" not in headers
