# Cognitive Logic — RC 1.0 Reproducible Build Report

- Date: 2026-08-01T00:23:00+02:00
- Commit: 2a22250f8bdff2919b548296be3ba1dad42a3bc5
- Branch: main
- Temporary environment: `/tmp/cognitivelogic-rc1-build/venv`

## Scope

A clean Python environment was created outside the repository.
The active production environment at `/app/cognitivelogic/venv/` was not modified.

## Installation results

- Core Flask requirements: **PASS**
- Reconciliation requirements: **PASS**
- Bolkestein requirements: **PASS**
- HoReCa auditor requirements: **PASS**
- Dependency consistency with `pip check`: **PASS**
- Python syntax compilation: **PASS**
- Pytest available from declared requirements: **NO**
- Node clean install and build: **PASS**

## Sovereign dependency finding

`qen-horeca-auditor/requirements.txt` declares:

```text
1:anthropic>=0.28.0
```

This dependency is classified as a legacy provider dependency.
It must not be removed until the HoReCa auditor source is reconciled with QEN Sovereign and tested.

## Build evidence

- Raw build log: `/tmp/cognitivelogic-rc1-build/phase-2-build.log`
- Installed package snapshot: `/tmp/cognitivelogic-rc1-build/pip-freeze.txt`

The raw log and temporary environment are local execution artifacts and are not committed.

## Release assessment


**BUILD BASELINE: PASS WITH SOVEREIGN DEPENDENCY FINDING**

## Test dependency reconciliation

A dedicated test dependency file was added:

```text
requirements-test.txt
```

Verified pytest version:

```text
pytest==8.4.2
```

Results:

- Test dependency installation: **PASS**
- Test collection: **PASS**
- Full test execution: **PASS**
- Playwright classification: **REFERENCED — REQUIRES SEPARATE TOOL REQUIREMENTS**

The production requirements remain separate from development and test dependencies.
