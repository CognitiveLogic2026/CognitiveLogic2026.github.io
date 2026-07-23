# Repository Impact Assessment

## Critical files

- `main.py`
- `orchestrator.py`
- `tests/test_orchestrator.py`
- `tests/test_smoke.py`
- `requirements-flask.txt`
- `.github/workflows/deploy-vps.yml`
- `.github/workflows/test.yml`

## Secondary files

- `qen-bolkestein/qen_config.py`
- `qen-bolkestein/qen_multi_agent_router.py`
- `qen-bolkestein/requirements.txt`
- `qen-horeca-auditor/requirements.txt`
- `qen_context.py`
- `README.md`
- `llms.txt`
- `VALIDATION_STATUS.md`
- commercial and architectural evidence documents.

## Public compatibility surface

Potentially affected routes include:

- `/classify-risk`
- `/copilot-analyze`
- `/gemini/qen-score`
- `/gemini/compliance-audit`
- `/agents/compliance-auditor`
- `/agents/territorial-mapper`
- `/agents/advisory-council`
- `/agents/mistral-compliance`
- `/agents/mistral-advisor`
- `/agents/openai-advisor`
- `/agents/bolkestein-assessment`
- `/agents/score-businesses`
- `/agents/places-batch-qen`

## Unaffected sovereign foundations

Expected to remain authoritative:

- reconciliation API;
- EVIDE chain;
- deterministic audit endpoints;
- graph datasets;
- QEN scoring models;
- governance records.
