import copy
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

import source_retrieval
from main import _copilot_cache_context, app, check_duplicate, limiter
from sovereign_engine import RISK_RULES, classify_risk, qen_score
from source_retrieval import RegistryError, build_index, load_index, load_registry, retrieve


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "source-registry.json"
INDEX = ROOT / "data" / "source-index.json"
COPILOT = ROOT / "copilot.html"

EXPECTED = {
    "DFV-002": "https://cognitivelogic.it/manifesto-verita-verificabile/",
    "OBS-BOLK-001": "https://cognitivelogic.it/resources/documents/osservatorio-bolkestein/",
    "AGCM-AS1930-NOTE-001": "https://cognitivelogic.it/resources/documents/concessioni-balneari-criteri-agcm/",
    "BEN-EGEA-QEN-001": "https://cognitivelogic.it/resources/documents/bolkestein-egea-benchmark/",
    "EA-009": "https://cognitivelogic.it/resources/documents/coste360-ea-009/",
    "CS-010": "https://cognitivelogic.it/resources/documents/cs-010-coastal-governance-intelligence/",
}

QUERIES = {
    "DFV-002": "DFV-002 Manifesto verità verificabile dodici tesi",
    "OBS-BOLK-001": "Osservatorio Bolkestein concessioni balneari",
    "AGCM-AS1930-NOTE-001": "AGCM AS1930 esperienza incumbent",
    "BEN-EGEA-QEN-001": "benchmark Egea QEN KPI normalizzati",
    "EA-009": "EA-009 EV-0001 validation evidence catalogue",
    "CS-010": "CS-010 Coastal Governance Intelligence",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_source_registry_is_valid_and_enforces_decision_boundary():
    registry = load_registry()
    assert registry["allowlist_enforced"] is True
    assert set(EXPECTED) <= {source["source_id"] for source in registry["sources"]}
    for source in registry["sources"]:
        assert {"modify_qen_configuration", "modify_qen_decisions"} <= set(source["prohibited_use"])
        assert source["sha256"] == sha256(ROOT / source["source_path"])


def test_loader_rejects_path_not_in_repository_allowlist(tmp_path):
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    source = copy.deepcopy(registry["sources"][0])
    source["source_id"] = "UNREGISTERED"
    source["source_path"] = "../../outside.md"
    registry["sources"].append(source)
    candidate = tmp_path / "registry.json"
    candidate.write_text(json.dumps(registry), encoding="utf-8")
    with pytest.raises(RegistryError, match="escapes repository"):
        load_registry(candidate)


def test_all_sources_load_and_generated_index_is_reproducible(tmp_path):
    first = build_index(destination=tmp_path / "one.json")
    second = build_index(destination=tmp_path / "two.json")
    assert first == second
    assert [doc["source_id"] for doc in first["documents"]] == [
        source["source_id"] for source in load_registry()["sources"] if source["enabled"]
    ]
    assert (tmp_path / "one.json").read_bytes() == (tmp_path / "two.json").read_bytes()


@pytest.mark.parametrize("source_id", EXPECTED)
def test_retrieval_returns_each_governed_content(source_id):
    result = retrieve(QUERIES[source_id])
    match = next(source for source in result["sources"] if source["source_id"] == source_id)
    assert result["retrieval_status"] == "ready"
    assert match["canonical_url"] == EXPECTED[source_id]
    assert match["source_class"] in {"primary", "secondary"}
    assert match["section"] and match["excerpt"]


def test_agcm_is_partial_secondary_orientation_not_case_study_or_judgment():
    result = retrieve("AGCM AS1930")
    source = next(item for item in result["sources"] if item["source_id"] == "AGCM-AS1930-NOTE-001")
    assert source["category"] == "provvedimento o orientamento AGCM"
    assert source["source_class"] == "secondary"
    assert any("case study completo" in warning for warning in source["warnings"])


def test_unapproved_benchmark_proposal_is_explicit():
    source = next(item for item in retrieve("Egea proposta non approvata")["sources"] if item["source_id"] == "BEN-EGEA-QEN-001")
    assert source["category"] == "benchmark proprietario"
    assert any("non sono approvati" in warning for warning in source["warnings"])


def test_manifesto_is_citable_by_section_and_not_confused_with_historical_dfv_001():
    result = retrieve("DFV-002 QEN Sovereign architettura della verificabilità")
    source = next(item for item in result["sources"] if item["source_id"] == "DFV-002")
    assert source["canonical_url"] == EXPECTED["DFV-002"]
    assert source["section"]
    assert "DFV-001" not in {item["source_id"] for item in result["sources"]}
    registry = load_registry()
    assert "DFV-001" not in {item["source_id"] for item in registry["sources"]}
    theses = next(item for item in retrieve("dodici tesi della verità verificabile")["sources"] if item["source_id"] == "DFV-002")
    infrastructure = next(item for item in retrieve("Dalla cultura all’infrastruttura QEN Sovereign")["sources"] if item["source_id"] == "DFV-002")
    assert theses["section"].startswith("17.")
    assert infrastructure["section"].startswith("16.")


def test_primary_official_source_is_preferred_when_equally_relevant(monkeypatch):
    base = json.loads(INDEX.read_text(encoding="utf-8"))
    observed = next(document for document in base["documents"] if document["source_id"] == "OBS-BOLK-001")
    primary = copy.deepcopy(observed)
    secondary = copy.deepcopy(observed)
    primary["source_id"] = "OFFICIAL"
    primary["metadata"]["source_class"] = "primary"
    secondary["source_id"] = "COMMENTARY"
    secondary["metadata"]["source_class"] = "secondary"
    fake = {**base, "documents": [secondary, primary]}
    monkeypatch.setattr(source_retrieval, "load_index", lambda *args, **kwargs: (fake, "ready"))
    monkeypatch.setattr(source_retrieval, "knowledge_version", lambda: {"registry_version": "test", "index_version": "test", "retrieval_status": "ready"})
    assert retrieve("Osservatorio Bolkestein")["sources"][0]["source_id"] == "OFFICIAL"


def test_no_invented_citations():
    registry = load_registry()
    allowed = {source["source_id"]: source["canonical_url"] for source in registry["sources"] if source["enabled"]}
    for query in QUERIES.values():
        for source in retrieve(query)["sources"]:
            assert allowed[source["source_id"]] == source["canonical_url"]


@pytest.mark.parametrize("source_id", EXPECTED)
def test_document_to_registry_to_loader_to_index_to_api_to_ui_citation(source_id):
    registry = load_registry()
    record = next(source for source in registry["sources"] if source["source_id"] == source_id)
    assert (ROOT / record["source_path"]).is_file()
    index, status = load_index()
    assert status == "ready"
    assert source_id in {doc["source_id"] for doc in index["documents"]}

    with patch("main.check_duplicate", return_value=None), patch("main.save_pilot"):
        response = app.test_client().post(
            "/copilot-analyze",
            json={"description": QUERIES[source_id]},
            headers={"Origin": "https://cognitivelogic.it"},
        )
    assert response.status_code == 200
    payload = response.get_json()
    citation = next(source for source in payload["sources"] if source["source_id"] == source_id)
    assert citation["canonical_url"] == EXPECTED[source_id]
    assert payload["response_mode"] == "sovereign"
    ui = COPILOT.read_text(encoding="utf-8")
    for field in ("canonical_url", "category", "authority", "date", "source_class", "confidence", "section", "warnings"):
        assert f"source.{field}" in ui


def test_api_propagates_retrieval_contract():
    with patch("main.check_duplicate", return_value=None), patch("main.save_pilot"):
        response = app.test_client().post(
            "/copilot-analyze", json={"description": "EA-009 EV-0001"},
            headers={"Origin": "https://cognitivelogic.it"},
        )
    payload = response.get_json()
    assert {"sources", "uncertainty", "confidence", "retrieval_status", "knowledge_version", "response_mode"} <= payload.keys()


def test_ui_fallback_is_transparent_and_does_not_invoke_local_analysis():
    ui = COPILOT.read_text(encoding="utf-8")
    catch_block = ui[ui.index("} catch (err) {"):ui.index("\n      try {", ui.index("} catch (err) {"))]
    assert "Modalità fallback" in catch_block
    assert "localAnalyze(text)" not in catch_block
    assert "powered by QEN Sovereign" not in catch_block


def test_cache_is_invalidated_when_context_changes(monkeypatch):
    monkeypatch.setattr("main.load_pilot", lambda name: {"cache_context": {"engine_version": "old"}, "data": {}})
    assert check_duplicate("entity", {"engine_version": "new"}) is None


def test_documentary_dfv_002_contract_and_no_risk_classification():
    with patch("main.check_duplicate", return_value=None), patch("main.save_pilot"), \
         patch("main.sovereign_classify_risk") as classify:
        response = app.test_client().post(
            "/copilot-analyze",
            json={"description": "Cos’è il Manifesto della Verità Verificabile DFV-002?"},
            headers={"Origin": "https://cognitivelogic.it"},
        )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["interaction_mode"] == "documentary"
    assert payload["sources"][0]["source_id"] == "DFV-002"
    assert payload["sources"][0]["canonical_url"] == EXPECTED["DFV-002"]
    assert "verità assoluta" in payload["summary"]
    assert {"risk_level", "risk_score", "gdpr_risk", "eu_classification", "gaps", "recommendations"}.isdisjoint(payload)
    classify.assert_not_called()
    limiter.reset()


def test_operational_credit_scoring_remains_compliance():
    with patch("main.check_duplicate", return_value=None), patch("main.save_pilot"):
        response = app.test_client().post(
            "/copilot-analyze",
            json={"description": "Sistema di scoring creditizio automatizzato per approvare prestiti"},
            headers={"Origin": "https://cognitivelogic.it"},
        )
    payload = response.get_json()
    assert payload["interaction_mode"] == "compliance"
    assert "risk_level" in payload
    limiter.reset()


def test_documentary_cache_contract_invalidates_low_and_separates_queries(monkeypatch):
    old = {"engine_version": "old", "data": {"risk_level": "LOW"}}
    monkeypatch.setattr("main.load_pilot", lambda name: {"cache_context": old, "data": old["data"]})
    dfv_context = _copilot_cache_context("Cos’è DFV-002?")
    assert dfv_context["contract_version"] == "2.0"
    assert check_duplicate("DFV-002", dfv_context) is None
    assert _copilot_cache_context("Cos’è DFV-002?") != _copilot_cache_context("Spiega EA-009")


def test_retrieval_does_not_change_qen_rules_or_approved_decisions():
    rules_before = copy.deepcopy(RISK_RULES)
    score_before = qen_score(80, 70, 60)
    classification_before = classify_risk("chatbot informativo")["risk_level"]
    graph_before = sha256(ROOT / "data" / "qen_graph_v4.json")
    adr_before = sha256(ROOT / "docs" / "runtime" / "QEN-SOVEREIGN-CERTIFICATION.md")
    retrieve("benchmark Egea QEN AGCM Bolkestein")
    assert RISK_RULES == rules_before
    assert qen_score(80, 70, 60) == score_before
    assert classify_risk("chatbot informativo")["risk_level"] == classification_before
    assert sha256(ROOT / "data" / "qen_graph_v4.json") == graph_before
    assert sha256(ROOT / "docs" / "runtime" / "QEN-SOVEREIGN-CERTIFICATION.md") == adr_before


def test_safe_degraded_states(tmp_path):
    assert load_index(index_path=tmp_path / "missing.json")[1] == "index_missing"
    stale = json.loads(INDEX.read_text(encoding="utf-8"))
    stale["registry_hash"] = "stale"
    stale_path = tmp_path / "stale.json"
    stale_path.write_text(json.dumps(stale), encoding="utf-8")
    assert load_index(index_path=stale_path)[1] == "index_stale"
    result = retrieve("zzzxxyyqqq")
    assert result["retrieval_status"] == "no_results"
    assert result["sources"] == []


CASE_ACCEPTANCE = {
    "Cos’è il catalogo Case Studies di Cognitive Logic?": "CASE-CATALOG-001",
    "Cos’è il caso Coste360?": "CASE-COSTE360-001",
    "Qual è la relazione tra Cognitive Logic e HVA-001?": "CASE-HVA-001",
    "Confronta Egea e QEN senza dichiarare una superiorità assoluta.": "CASE-EGEA-QEN-001",
    "Quali criteri AGCM sono stati contestati?": "CASE-AGCM-001",
    "Cos’è la proposta Coastal Governance?": "CASE-COASTAL-001",
    "Cosa documenta il caso Leeds Xylo Core?": "CASE-LEEDS-001",
    "Cosa risulta dalle fonti EEOC sul caso iTutorGroup?": "CASE-ITUTOR-001",
    "Quali aspetti del caso iTutorGroup non sono verificabili?": "CASE-ITUTOR-001",
    "Quale autorità umana conserva la decisione finale?": "CASE-COASTAL-001",
}


@pytest.mark.parametrize(("query", "source_id"), CASE_ACCEPTANCE.items())
def test_case_study_acceptance_queries_return_governed_case(query, source_id):
    result = retrieve(query)
    assert result["retrieval_status"] == "ready"
    source = next(item for item in result["sources"] if item["source_id"] == source_id)
    assert {
        "PUBLIC EVIDENCE", "PRIMARY SOURCE", "ASSESSMENT INFERENCE",
        "NOT VERIFIABLE", "HUMAN DECISION REQUIRED",
    } <= set(source["evidence_labels"])
    assert source["limitations"]
    assert source["source_uncertainty"]
    assert source["final_human_authority"]


def test_case_pages_and_official_primary_sources_are_registered():
    registry = load_registry()
    urls = {source["canonical_url"] for source in registry["sources"]}
    assert {
        "https://cognitivelogic.it/case-studies/",
        "https://cognitivelogic.it/case-studies/cognitive-logic/",
        "https://cognitivelogic.it/case-studies/external/",
        *{f"https://cognitivelogic.it/case-studies/{slug}/" for slug in (
            "coste360", "hva-001", "egea-qen", "agcm-criteri-contestati",
            "coastal-governance", "leeds-xylo-core", "itutorgroup-screening",
        )},
        "https://www.gov.uk/algorithmic-transparency-records/leeds-city-council-xylo-core",
        "https://www.eeoc.gov/newsroom/eeoc-sues-itutorgroup-age-discrimination",
        "https://www.eeoc.gov/newsroom/itutorgroup-pay-365000-settle-eeoc-discriminatory-hiring-suit",
    } <= urls


def test_case_documentary_api_exposes_evidence_boundaries_and_human_authority():
    with patch("main.check_duplicate", return_value=None), patch("main.save_pilot"):
        response = app.test_client().post(
            "/copilot-analyze",
            json={"description": "Cos’è il caso Coste360?"},
            headers={"Origin": "https://cognitivelogic.it"},
        )
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["response_mode"] == "sovereign"
    assert payload["retrieval_status"] == "ready"
    assert "HUMAN DECISION REQUIRED" in payload["evidence_classes"]
    assert payload["source_limitations"]
    assert payload["human_decision_authority"]
    limiter.reset()


@pytest.mark.parametrize("query", CASE_ACCEPTANCE)
def test_all_case_acceptance_queries_use_documentary_sovereign_api(query):
    with patch("main.check_duplicate", return_value=None), patch("main.save_pilot"):
        response = app.test_client().post(
            "/copilot-analyze", json={"description": query},
            headers={"Origin": "https://cognitivelogic.it"},
        )
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["interaction_mode"] == "documentary"
    assert payload["response_mode"] == "sovereign"
    assert payload["retrieval_status"] == "ready"
    assert payload["knowledge_version"]["index_version"]
    assert payload["sources"]
    assert payload["confidence"] in {"medium", "high"}
    assert payload["uncertainty"]
    assert payload["limitations"]
    assert payload["human_decision_authority"]
    limiter.reset()
