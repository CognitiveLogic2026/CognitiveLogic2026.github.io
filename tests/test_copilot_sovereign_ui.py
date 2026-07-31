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
