from main import app


def _headers(response):
    return {key.lower(): value for key, value in response.headers.items()}


def test_mistral_compliance_is_deprecated():
    client = app.test_client()

    response = client.post(
        "/agents/mistral-compliance",
        json={"entity_name": "Test"},
    )

    headers = _headers(response)

    assert headers["deprecation"] == "true"
    assert headers["x-qen-compatibility-route"] == "legacy-provider-agent"
    assert (
        '</agents/compliance-auditor>; rel="successor-version"'
        in headers["link"]
    )


def test_mistral_advisor_is_deprecated():
    client = app.test_client()

    response = client.post(
        "/agents/mistral-advisor",
        json={"entity_name": "Test"},
    )

    headers = _headers(response)

    assert headers["deprecation"] == "true"
    assert headers["x-qen-compatibility-route"] == "legacy-provider-agent"
    assert (
        '</agents/advisory-council>; rel="successor-version"'
        in headers["link"]
    )


def test_sovereign_agent_is_not_marked_legacy():
    client = app.test_client()

    response = client.post(
        "/agents/compliance-auditor",
        json={"entity_name": "Test"},
    )

    headers = _headers(response)

    assert "x-qen-compatibility-route" not in headers
