# QEN Sovereign Intelligence — Architectural Analysis

Date: 2026-07-23  
Status: COMPLETE  
Implementation authorized: NO

## Finding

The current repository is not yet sovereign.

External AI providers remain embedded in:

- runtime decision paths;
- Flask endpoints;
- orchestration logic;
- dependency declarations;
- CI tests;
- VPS deployment secrets;
- documentation and public architecture descriptions.

## Primary evidence

### Runtime

`main.py` contains:

- Anthropic SDK initialization;
- Claude calls for classification and copilot analysis;
- Gemini REST calls;
- `/gemini/qen-score`;
- `/gemini/compliance-audit`.

`orchestrator.py` contains:

- Anthropic client initialization;
- Mistral REST calls;
- Claude fallback logic;
- provider-selectable scoring;
- provider-specific public endpoints.

`qen-bolkestein` contains:

- Anthropic imports;
- Mistral dependencies;
- provider routing.

### CI and deployment

`.github/workflows/deploy-vps.yml` injects:

- ANTHROPIC_API_KEY;
- GOOGLE_API_KEY;
- MISTRAL_API_KEY;
- OPENAI_API_KEY.

`requirements-flask.txt`, `qen-horeca-auditor/requirements.txt` and
`qen-bolkestein/requirements.txt` declare external provider SDKs.

### Tests

The test suite mocks Anthropic, Gemini and Mistral and verifies provider
fallback behaviour. These tests encode the previous architecture.

## Sovereign assets already present

The repository already contains foundations for a sovereign architecture:

- QEN scoring engines;
- Knowledge Graph datasets;
- QEN reconciliation;
- EVIDE registration and chain;
- deterministic HoReCa and balneare audit logic;
- governance and evidence structures;
- proprietary KPI models.

## Architectural conclusion

The required transformation is a controlled replacement of external
provider decision paths with deterministic, evidence-based QEN services.

External data sources may remain admissible as evidence inputs where
governed, but external AI models must not determine classifications,
scores, verdicts or recommendations.
