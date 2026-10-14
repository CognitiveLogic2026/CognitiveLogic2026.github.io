
from pathlib import Path

HTML = Path("restaurant-assessment/index.html")

def source():
    return HTML.read_text(encoding="utf-8")

def test_decision_memory_optional():
    text = source()
    section = text.split(
        '<section id="decisionMemory"',1
    )[1].split('</section>',1)[0]
    assert 'required' not in section
    for name in ("supplier","menu","shifts"):
        assert 'name="dm_' + name + '"' in section

def test_decision_memory_preserves_scoring():
    text = source()
    script = text.split(
        '<script id="decision-memory-layer">',1
    )[1].split('</script>',1)[0]
    for forbidden in (
        "dimensionScores",
        "evidenceCoverage",
        "totalScore",
        "localStorage",
        "fetch("
    ):
        assert forbidden not in script

def test_decision_memory_email_consent():
    text = source()
    assert 'id="decisionMemoryIncludeEmail"' in text
    assert 'if(!consent || !consent.checked) return []' in text
    assert 'window.cognitiveLogicDecisionMemoryEmailLines()' in text
    assert 'DECLARED — non verificato' in text
