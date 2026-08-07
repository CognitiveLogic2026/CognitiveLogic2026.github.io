"""Regression tests for removed Gemini compatibility namespace."""

from main import app


def test_legacy_gemini_qen_score_removed():
    client = app.test_client()
    response = client.post(
        "/gemini/qen-score",
        json={
            "business_name": "Legacy Test",
            "sector": "test",
            "description": "legacy namespace test",
        },
    )
    assert response.status_code == 404


def test_legacy_gemini_compliance_audit_removed():
    client = app.test_client()
    response = client.post(
        "/gemini/compliance-audit",
        json={
            "system_name": "Legacy Test",
            "description": "legacy namespace test",
        },
    )
    assert response.status_code == 404


def test_canonical_qen_score_route_exists():
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/qen-score" in rules


def test_canonical_compliance_route_exists():
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/compliance-audit" in rules


def test_gemini_namespace_absent():
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert not any(rule.startswith("/gemini/") for rule in rules)
