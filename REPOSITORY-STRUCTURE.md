# Cognitive Logic — Repository Structure

## Purpose
Operational map of the Cognitive Logic repository. Do not move, delete, or consolidate files without checking runtime, web, deployment, Git, and documentation dependencies.

## 1. Public web / production
Root HTML/XML/TXT files plus `css/`, `js/`, `img/`, `assets/`, `fonts/`, `static/`, and `resources/` may map directly to production URLs.
Rule: verify Nginx, internal links, canonical URLs, sitemap, and HTTP responses before moving them.

## 2. QEN runtime
Core runtime: `main.py`, `orchestrator.py`, `sovereign_engine.py`, `qen_context.py`, `source_retrieval.py`, `wizard.py`.
Runtime data may include `graph.json`, `pilots.json`, `pilots.json.lock`, and `escalations.json`; these are intentionally ignored by Git.
Related modules: `qen-bolkestein/`, `qen-enterprise-assessment/`, `qen-horeca-auditor/`, `qen-reconciliation/`, `qencode/`, `wizard-src/`.
Rule: an ignored runtime file is not automatically disposable.

## 3. QEN Sovereign
Primary product area: `qen-sovereign/`.
Contains product documentation, governed knowledge sources, validation evidence, and public presentation assets.
Rule: preserve traceability between software, governance documentation, and validation evidence.

## 4. Commercial platform
Commercial areas include `digital-presence/`, `commercial-evolution-1.0/`, `commercial-platform/`, `commercial-service-catalogue/`, `enterprise-platform-evolution-1.0/`, `editorial-evolution-1.0/`, `executive-assets/`, and `case-studies/`.

## 5. Research and monitoring
`international-watch/`, `research/`, `data/`, and `schemas/` contain research, datasets, structured evidence, and governed records.
Rule: do not treat research/data files as build artifacts without checking provenance and downstream use.

## 6. Documentation and history
Current documentation includes `docs/`, `documentation-audit/`, `README.md`, `AUDIT_LOG.md`, `VALIDATION_STATUS.md`, and release documents.
Historical technical records include `sovereign-intelligence-refactor-1.0/`, `sovereign-intelligence-refactor-2.0/`, `rc1-audit-closure/`, and `housekeeping-2026/`.
Rule: historical directories are retained even when not required by runtime.

## 7. SIAE deposit baselines
Official deposit material is under `siae/`.
QEN Sovereign 1.0.0 baseline: `siae/QEN-Sovereign-1.0.0/`.
Deposited baselines are immutable. Future releases must use a new version directory.
The baseline may contain files globally ignored by Git, including `package/source/graph.json`; do not delete them.

Private delivery archive:
`/root/cognitivelogic-archive/siae/QEN-Sovereign-1.0.0/`

QEN Sovereign 1.0.0 delivery ZIP SHA-256:
`6%1a91375ecea3502b48fc4defc7b7e777ef3c84049fbc106e28324b45dcfbd2`

Baseline `package/source/graph.json` SHA-256:
`59fe15d66d4a71af1e5d4c2fa570500d285bd54f352beac0af75e0cd3160bc9c`

## 8. Local / non-versioned environments
`venv/`, `wizard-src/node_modules/`, `logs/`, `downloads/`, Python caches, and pytest caches are local/runtime artifacts and should normally remain outside Git.

## 9. Safe maintenance procedure
Before deleting or moving an uncertain file:
1. check whether Git tracks it;
2. check `.gitignore`;
3. search repository references;
4. determine whether it is runtime-generated;
5. determine whether it belongs to an evidentiary or SIAE baseline;
6. compare SHA-256 when duplicate identity matters;
7. make the smallest possible change;
8. verify `git status`;
9. test affected production URLs/services.

Never perform mass deletion based only on filename similarity.

## 10. Maintenance status — 2026-08-26
Repository housekeeping completed. Temporary backups and caches were removed, the accidental empty `127.0.0.1:8765` directory was removed, duplicate analysis was completed, Sovereign refactor history was retained, secret-pattern scans were performed on current refactor files and their Git history, the SIAE delivery archive was preserved independently, Git was clean, and production endpoints returned HTTP 200 after cleanup.
