"""Smoke tests for Flask (port 5000) and FastAPI (port 8001) endpoints.

Runs against the app objects directly (no live server needed).
The anthropic module is mocked before Flask app import to avoid needing a
real ANTHROPIC_API_KEY in CI.
"""
import importlib.util
import os
import sys
from unittest.mock import MagicMock

import pytest

# ── Mock anthropic before importing Flask app (client instantiated at module level) ──
_mock_anthropic = MagicMock()
sys.modules["anthropic"] = _mock_anthropic

# ── Flask app ────────────────────────────────────────────────────────────────────────
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _repo_root)
import main as _flask_main  # noqa: E402  (top-level main.py is the Flask app)

flask_client = _flask_main.app.test_client()

# ── FastAPI app (qen-reconciliation/main.py) ─────────────────────────────────────────
from fastapi.testclient import TestClient  # noqa: E402

_reconciliation_path = os.path.join(_repo_root, "qen-reconciliation", "main.py")
_spec = importlib.util.spec_from_file_location("reconciliation_main", _reconciliation_path)
_reconciliation_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_reconciliation_mod)

fastapi_client = TestClient(_reconciliation_mod.app)


# ── Flask tests ───────────────────────────────────────────────────────────────────────

def test_flask_health():
    resp = flask_client.get("/health")
    assert resp.status_code == 200


def test_flask_pilots():
    resp = flask_client.get("/pilots")
    assert resp.status_code == 200


# ── FastAPI tests ─────────────────────────────────────────────────────────────────────

def test_fastapi_health():
    resp = fastapi_client.get("/health")
    assert resp.status_code == 200


def test_fastapi_root():
    resp = fastapi_client.get("/")
    assert resp.status_code in (200, 404), f"Unexpected status: {resp.status_code}"
