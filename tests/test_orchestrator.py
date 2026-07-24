"""Tests for the 11 orchestrator agent endpoints.

All external I/O (Anthropic, Mistral, Google Places, file reads) is mocked so
tests run without live API keys or network access.

Helper functions (_get_client, _places_discover, _score_business_list,
_requests) live in orchestrator.py, so patches target that module.
"""
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── bootstrap identical to test_smoke.py ────────────────────────────────────
_mock_anthropic = MagicMock()
sys.modules["anthropic"] = _mock_anthropic

os.environ["COGNITIVE_API_KEY"] = "test-key-ci"
os.environ["SUPERVISOR_KEY"] = "test-supervisor-ci"

_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _repo_root)
import main as _flask_main  # noqa: E402
import orchestrator as _orch  # noqa: E402

client = _flask_main.app.test_client()

# ── helpers ──────────────────────────────────────────────────────────────────

_VALID_JSON_AUDIT = json.dumps({
    "compliance_score": 75,
    "risk_level": "MEDIUM",
    "summary": "ok",
    "recommendations": [],
    "gaps": [],
})

_VALID_JSON_ADVISORY = json.dumps({
    "strategic_advice": "ok",
    "priority_actions": [],
    "timeline": "Q1",
    "investment_estimate": "10k",
})

_VALID_JSON_TERRITORIAL = json.dumps({
    "territorial_score": 80,
    "market_potential": "HIGH",
    "summary": "ok",
    "opportunities": [],
})

_VALID_JSON_BOLKESTEIN = json.dumps({
    "bolkestein_risk": "LOW",
    "compliance_score": 90,
    "summary": "ok",
    "action_plan": [],
})

_BASE_PAYLOAD = {
    "entity_name": "Test SRL",
    "description": "Software per la gestione aziendale.",
    "sector": "tech",
}


def _make_claude_mock(text: str):
    """Return a mock for _get_client().messages.create(...)."""
    mock_client = MagicMock()
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    mock_client.return_value.messages.create.return_value = msg
    return mock_client


def _make_mistral_response(text: str):
    """Return a mock requests.Response for Mistral chat completions."""
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {
        "choices": [{"message": {"content": text}}]
    }
    return resp


# ── 1. compliance-auditor ─────────────────────────────────────────────────────

class TestComplianceAuditor:
    def test_missing_description_returns_400(self):
        resp = client.post("/agents/compliance-auditor", json={"entity_name": "X"})
        assert resp.status_code == 400

    def test_success(self):
        with patch.object(_orch, "_get_client", _make_claude_mock(_VALID_JSON_AUDIT)):
            resp = client.post("/agents/compliance-auditor", json=_BASE_PAYLOAD)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"
        assert "audit" in data
        assert data["audit"]["entity_name"] == "Test SRL"


# ── 2. territorial-mapper ─────────────────────────────────────────────────────

class TestTerritorialMapper:
    def test_missing_description_returns_400(self):
        resp = client.post("/agents/territorial-mapper", json={"entity_name": "X"})
        assert resp.status_code == 400

    def test_success(self):
        with patch.object(_orch, "_get_client", _make_claude_mock(_VALID_JSON_TERRITORIAL)):
            with patch.object(_orch, "_places_enrich", return_value=""):
                resp = client.post("/agents/territorial-mapper", json=_BASE_PAYLOAD)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"
        assert "mapping" in data


# ── 3. advisory-council ───────────────────────────────────────────────────────

class TestAdvisoryCouncil:
    def test_missing_description_returns_400(self):
        resp = client.post("/agents/advisory-council", json={"entity_name": "X"})
        assert resp.status_code == 400

    def test_success(self):
        with patch.object(_orch, "_get_client", _make_claude_mock(_VALID_JSON_ADVISORY)):
            resp = client.post("/agents/advisory-council", json={**_BASE_PAYLOAD, "risk_level": "LOW"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"
        assert "advisory" in data


# ── 4. intelligence-feed ──────────────────────────────────────────────────────

class TestIntelligenceFeed:
    def test_get_returns_200_with_status_ok(self):
        feed_json = json.dumps({"feed": [], "benchmarks": {}})
        with patch.object(Path, "read_text", return_value=feed_json):
            resp = client.get("/agents/intelligence-feed")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert "timestamp" in data

    def test_file_missing_returns_empty_feed(self):
        with patch.object(Path, "read_text", side_effect=FileNotFoundError):
            resp = client.get("/agents/intelligence-feed")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["feed"] == []


# ── 5. mistral-compliance ────────────────────────────────────────────────────

class TestMistralCompliance:
    def test_missing_description_returns_400(self):
        with patch.dict(os.environ, {"MISTRAL_API_KEY": "fake"}):
            resp = client.post("/agents/mistral-compliance", json={"entity_name": "X"})
        assert resp.status_code == 400

    def test_no_key_returns_503(self):
        env = {k: v for k, v in os.environ.items() if k != "MISTRAL_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            resp = client.post("/agents/mistral-compliance", json=_BASE_PAYLOAD)
        assert resp.status_code == 503

    def test_success_via_mistral(self):
        mock_requests = MagicMock()
        mock_requests.post.return_value = _make_mistral_response(_VALID_JSON_AUDIT)
        with patch.dict(os.environ, {"MISTRAL_API_KEY": "fake"}):
            with patch.object(_orch, "_requests", mock_requests):
                resp = client.post("/agents/mistral-compliance", json=_BASE_PAYLOAD)
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "success"


# ── 6. mistral-advisor ───────────────────────────────────────────────────────

class TestMistralAdvisor:
    def test_missing_description_returns_400(self):
        with patch.dict(os.environ, {"MISTRAL_API_KEY": "fake"}):
            resp = client.post("/agents/mistral-advisor", json={"entity_name": "X"})
        assert resp.status_code == 400

    def test_no_key_returns_503(self):
        env = {k: v for k, v in os.environ.items() if k != "MISTRAL_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            resp = client.post("/agents/mistral-advisor", json=_BASE_PAYLOAD)
        assert resp.status_code == 503

    def test_success_via_mistral(self):
        mock_requests = MagicMock()
        mock_requests.post.return_value = _make_mistral_response(_VALID_JSON_ADVISORY)
        with patch.dict(os.environ, {"MISTRAL_API_KEY": "fake"}):
            with patch.object(_orch, "_requests", mock_requests):
                resp = client.post("/agents/mistral-advisor", json={**_BASE_PAYLOAD, "risk_level": "HIGH"})
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "success"


# ── 7. openai-advisor (disabled) ─────────────────────────────────────────────

class TestOpenAIAdvisor:
    def test_always_returns_503(self):
        resp = client.post("/agents/openai-advisor", json=_BASE_PAYLOAD)
        assert resp.status_code == 503
        assert resp.get_json()["error"] == "endpoint_disabled"


# ── 8. bolkestein-assessment ─────────────────────────────────────────────────

class TestBolkesteinAssessment:
    def test_missing_description_returns_400(self):
        resp = client.post("/agents/bolkestein-assessment", json={"entity_name": "X"})
        assert resp.status_code == 400

    def test_success_via_mistral(self):
        mock_requests = MagicMock()
        mock_requests.post.return_value = _make_mistral_response(_VALID_JSON_BOLKESTEIN)
        with patch.dict(os.environ, {"MISTRAL_API_KEY": "fake"}):
            with patch.object(_orch, "_requests", mock_requests):
                resp = client.post("/agents/bolkestein-assessment", json={
                    **_BASE_PAYLOAD,
                    "concessione_tipo": "demanio",
                    "scadenza_attuale": "2027-12-31",
                })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"
        assert data["assessment"]["deadline_2027"] == "2027-01-01"


# ── 9. places-discovery ───────────────────────────────────────────────────────

class TestPlacesDiscovery:
    def test_no_key_returns_503(self):
        env = {k: v for k, v in os.environ.items() if k != "GOOGLE_PLACES_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            resp = client.post("/agents/places-discovery", json={"comune": "Bologna"})
        assert resp.status_code == 503

    def test_success(self):
        fake_businesses = [{"name": "Bar Roma", "place_id": "abc123"}]
        with patch.dict(os.environ, {"GOOGLE_PLACES_API_KEY": "fake"}):
            with patch.object(_orch, "_places_discover", return_value=fake_businesses):
                resp = client.post("/agents/places-discovery", json={"comune": "Bologna", "settore": "horeca"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"
        assert data["total"] == 1


# ── 10. score-businesses ──────────────────────────────────────────────────────

class TestScoreBusinesses:
    def test_empty_list_returns_success(self):
        with patch.object(_orch, "_score_business_list", return_value=[]):
            resp = client.post("/agents/score-businesses", json={"businesses": []})
        assert resp.status_code == 200
        assert resp.get_json()["total"] == 0

    def test_success_with_businesses(self):
        scored = [{"name": "Bar Roma", "qen_score": 72.5}]
        with patch.object(_orch, "_score_business_list", return_value=scored):
            resp = client.post("/agents/score-businesses", json={
                "businesses": [{"name": "Bar Roma"}],
                "provider": "mistral",
            })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"
        assert data["total"] == 1


# ── 11. places-batch-qen ─────────────────────────────────────────────────────

class TestPlacesBatchQen:
    def test_no_places_key_returns_503(self):
        env = {k: v for k, v in os.environ.items() if k != "GOOGLE_PLACES_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            resp = client.post("/agents/places-batch-qen", json={"comune": "Bologna"})
        assert resp.status_code == 503

    def test_empty_discovery_returns_empty_scored(self):
        with patch.dict(os.environ, {"GOOGLE_PLACES_API_KEY": "fake"}):
            with patch.object(_orch, "_places_discover", return_value=[]):
                resp = client.post("/agents/places-batch-qen", json={"comune": "Bologna"})
        assert resp.status_code == 200
        assert resp.get_json()["total"] == 0

    def test_success(self):
        businesses = [{"name": "Bar Roma"}]
        scored = [{"name": "Bar Roma", "qen_score": 68.0}]
        with patch.dict(os.environ, {"GOOGLE_PLACES_API_KEY": "fake"}):
            with patch.object(_orch, "_places_discover", return_value=businesses):
                with patch.object(_orch, "_score_business_list", return_value=scored):
                    resp = client.post("/agents/places-batch-qen", json={
                        "comune": "Bologna",
                        "settore": "horeca",
                        "max_results": 5,
                    })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"
        assert data["total"] == 1
        assert data["comune"] == "Bologna"


# ── audit/horeca & audit/balneare — auth ─────────────────────────────────────

class TestAuditAuth:
    _horeca_payload = {
        "azienda_nome": "Trattoria Test",
        "coperti": 60,
        "qen_score_finale": 72.5,
        "moduli_dettagliati": {
            "sociale": {"score": 70}, "governance": {"score": 75},
            "imballaggi": {"score": 80}, "risorse": {"score": 65},
            "qualita": {"score": 70}, "rifiuti": {"score": 60},
            "logistica": {"score": 75}, "territorio": {"score": 80},
        },
        "status_conformita": "CONFORME",
    }
    _balneare_payload = {
        "azienda_nome": "Lido Test",
        "tipo": "balneare",
        "qen_score_finale": 68.0,
        "scores": {"m1": 70, "m2": 65, "m3": 75, "m4": 60, "m5": 80, "m6": 55},
    }

    def test_horeca_no_key_returns_403(self):
        resp = client.post("/audit/horeca", json=self._horeca_payload)
        assert resp.status_code == 403

    def test_horeca_wrong_key_returns_403(self):
        resp = client.post("/audit/horeca", json=self._horeca_payload,
                           headers={"X-API-Key": "wrong"})
        assert resp.status_code == 403

    def test_horeca_correct_key_returns_200(self):
        with patch("main.save_pilot"), \
             patch("main._evide_append", return_value={"id": "evide-test"}):
            resp = client.post("/audit/horeca", json=self._horeca_payload,
                               headers={"X-API-Key": "test-key-ci"})
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "saved"

    def test_balneare_no_key_returns_403(self):
        resp = client.post("/audit/balneare", json=self._balneare_payload)
        assert resp.status_code == 403

    def test_balneare_correct_key_returns_200(self):
        with patch("main.save_pilot"), \
             patch("main._evide_append", return_value={"id": "evide-test"}):
            resp = client.post("/audit/balneare", json=self._balneare_payload,
                               headers={"X-API-Key": "test-key-ci"})
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "saved"


# ── gemini/compliance-audit ───────────────────────────────────────────────────

_VALID_COMPLIANCE_AUDIT = json.dumps({
    "system_name": "Test System",
    "risk_classification": "High-Risk",
    "domain": "HR",
    "assessment_date": "2026-05-31",
    "scores": {"Vs": 70, "Va": 65, "Vt": 75, "QEN_SCORE": 70.0},
    "findings": [],
    "mandatory_controls": [],
    "escalation_flag": False,
    "escalation_reason": None,
    "recommendation": "Conditional Approval",
    "next_steps": [],
    "governance_owner": "Legal",
    "review_date": "2026-08-29",
})

class TestComplianceAuditEndpoint:
    _payload = {
        "system_name": "AI Hiring Tool",
        "system_type": "ML classifier",
        "domain": "HR",
        "description": "Filtra i CV automaticamente per posizioni aperte.",
        "controls": "Nessuno",
    }

    _trusted = {"Origin": "https://www.cognitivelogic.it"}

    def test_missing_description_returns_400(self):
        resp = client.post("/gemini/compliance-audit", json={"system_name": "X"},
                           headers=self._trusted)
        assert resp.status_code == 400

    def test_success_via_gemini(self):
        mock_requests = MagicMock()
        gemini_resp = MagicMock()
        gemini_resp.raise_for_status = MagicMock()
        gemini_resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": _VALID_COMPLIANCE_AUDIT}]}}]
        }
        mock_requests.post.return_value = gemini_resp
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "fake"}):
            with patch("main._requests", mock_requests):
                resp = client.post("/gemini/compliance-audit", json=self._payload,
                                   headers=self._trusted)
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "success"


# ── origin check su endpoint cost-bearing ────────────────────────────────────

class TestTrustedOrigin:
    """_require_trusted_origin deve bloccare chiamate senza Origin/Referer noti
    a meno che non venga fornito X-API-Key valido."""

    def test_copilot_analyze_blocked_without_origin(self):
        resp = client.post("/copilot-analyze",
                           json={"description": "test"},
                           headers={})
        assert resp.status_code == 403

    _copilot_mock_text = ('{"allegato":"III","livello_rischio":"Minimo","gdpr_risk":"BASSO",'
                          '"motivazione":"ok","gdpr_motivazione":"ok","qen_impact":"low",'
                          '"articoli_rilevanti":[],"azioni_richieste":[],"vs":70,"va":65,"vt":75}')

    def test_copilot_analyze_allowed_with_trusted_origin(self):
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text=self._copilot_mock_text)]
        with patch("main.ANTHROPIC_CLIENT") as mock_client, \
             patch("main.check_duplicate", return_value=None), \
             patch("main.save_pilot"):
            mock_client.messages.create.return_value = mock_msg
            resp = client.post("/copilot-analyze",
                               json={"description": "test"},
                               headers={"Origin": "https://www.cognitivelogic.it"})
        assert resp.status_code == 200

    def test_copilot_analyze_allowed_with_api_key(self):
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text=self._copilot_mock_text)]
        with patch("main.ANTHROPIC_CLIENT") as mock_client, \
             patch("main.check_duplicate", return_value=None), \
             patch("main.save_pilot"):
            mock_client.messages.create.return_value = mock_msg
            resp = client.post("/copilot-analyze",
                               json={"description": "test"},
                               headers={"X-API-Key": "test-key-ci"})
        assert resp.status_code == 200

    def test_gemini_qen_score_blocked_without_origin(self):
        resp = client.post("/gemini/qen-score",
                           json={"description": "test"},
                           headers={})
        assert resp.status_code == 403

    def test_compliance_audit_blocked_without_origin(self):
        resp = client.post("/gemini/compliance-audit",
                           json={"description": "test"},
                           headers={})
        assert resp.status_code == 403
