# Cognitive Logic — RC 1.0 Repository Hygiene Report

- Status: Phase 1 completed with tracked-backup review pending
- Date: 2026-08-01T00:19:25+02:00
- Baseline commit: 6813bbdfb154e3239ccfa026bfe7d3d654ef8059
- Branch: main

## Completed actions

- Moved extracted audit packages outside the repository.
- Removed the unused `.venv-runtime/` environment.
- Retained the active production `venv/` environment.
- Removed reconstructible `wizard-src/node_modules/`.
- Archived untracked backup and temporary artifacts outside the repository.
- Removed untracked cache directories.
- Updated `.gitignore` for audit output and local runtime artifacts.

## Runtime decision

`venv/` is used by:

- `cognitivelogic.service`
- `cognitivelogic-flask.service`

It must remain on the operational server, but must be excluded from every RC distribution archive.

## Tracked backup finding


No tracked backup files remain.

## Sovereign dependency finding

- `qen-horeca-auditor/requirements.txt` still declares `anthropic>=0.28.0`.
- Active UI and documentation still contain Claude, Mistral and Gemini references.
- These findings are assigned to the Sovereign Reconciliation phases.

## Current repository size

```text
342M	.
```
