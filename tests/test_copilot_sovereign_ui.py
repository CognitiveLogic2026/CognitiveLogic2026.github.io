from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COPILOT = ROOT / "copilot.html"


def content() -> str:
    return COPILOT.read_text(encoding="utf-8")


def test_copilot_uses_qen_sovereign():
    assert "QEN Sovereign" in content()


def test_copilot_has_no_provider_selector():
    text = content()

    for token in (
        'id="btn-claude"',
        'id="btn-mistral"',
        'data-provider="claude"',
        'data-provider="mistral"',
        "activeProvider",
        "setProvider(",
        "normalizeMistral(",
    ):
        assert token not in text


def test_copilot_uses_single_endpoint():
    text = content()
    endpoint = "https://api.cognitivelogic.it/copilot-analyze"

    assert text.count(endpoint) == 1
    assert "agents/mistral-compliance" not in text
    assert "/gemini/" not in text


def test_copilot_uses_single_runtime_constant():
    text = content()

    assert (
        'const COPILOT_ENDPOINT = '
        '"https://api.cognitivelogic.it/copilot-analyze";'
    ) in text

    assert "const ENDPOINTS" not in text


def test_documentary_branch_precedes_risk_access_and_hides_compliance_cards():
    text = content()
    branch = text.index('if (d.interaction_mode === "documentary")')
    assert branch < text.index("d.risk_level", branch)
    documentary = text[text.index("function renderDocumentary"):text.index("function renderSources")]
    for card in ("risk-score-card", "compliance-rationale-card", "compliance-gaps-card", "recommendations-card"):
        assert card in documentary
    assert 'document.getElementById(id).hidden = true' in documentary
    assert "RISPOSTA DOCUMENTALE" in documentary
    assert "FONTE GOVERNATA" in documentary


def test_documentary_pdf_is_separate_and_has_no_compliance_fields():
    text = content()
    documentary_pdf = text[text.index("function exportDocumentaryPDF"):text.index("/* Legacy local demo engine")]
    assert "QEN Documentary Response" in documentary_pdf
    assert "QEN_Documentary_Response_" in documentary_pdf
    for forbidden in ("Risk Score", "EU AI ACT", "GDPR", "COMPLIANCE GAPS", "RECOMMENDATIONS"):
        assert forbidden not in documentary_pdf


def test_api_source_content_is_rendered_with_text_content():
    text = content()
    source_renderer = text[text.index("function renderSources"):text.index("btnAnalyze.addEventListener")]
    assert "source.excerpt" in source_renderer
    assert "excerpt.textContent" in source_renderer
    assert "innerHTML" not in source_renderer
