# Cognitive Logic — RC 1.0 Test Execution Report

- Date: 2026-08-01T00:26:10+02:00
- Commit tested: 2a22250f8bdff2919b548296be3ba1dad42a3bc5
- Branch: main
- Python: Python 3.12.3
- Pytest: 8.4.2
- Test source files: 4

## Environment

Tests were executed in a clean temporary virtual environment:

`/tmp/cognitivelogic-rc1-build/venv`

The production environment `/app/cognitivelogic/venv/` was not modified.

## Results

- Requirements installation: **PASS**
- Test collection: **PASS**
- Full suite: **PASS**
- Pytest exit code: **0**
- Dependency consistency: **PASS**

## Dependency classification

- Runtime dependencies remain in the existing component requirements.
- Test dependencies are declared in `requirements-test.txt`.
- Playwright status: **REFERENCED — REQUIRES SEPARATE TOOL REQUIREMENTS**
- Anthropic remains a legacy dependency in the HoReCa auditor and is assigned to Sovereign Reconciliation.

## Raw local evidence

`/tmp/cognitivelogic-rc1-build/phase-2b-tests.log`

The raw execution log is a local artifact and is not committed.

## Decision


**TEST INFRASTRUCTURE: PASS**
