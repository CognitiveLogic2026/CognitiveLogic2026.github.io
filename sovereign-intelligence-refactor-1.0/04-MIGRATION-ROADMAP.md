# QEN Sovereign Intelligence — Migration Roadmap

Status: PROPOSED  
Implementation authorized: NO

## Phase 1 — Baseline protection

- Capture Git baseline.
- Backup runtime files and systemd configuration.
- Record current endpoint contracts.
- Record current health checks.

## Phase 2 — Sovereign service boundary

Introduce authoritative internal services for:

- risk classification;
- QEN scoring;
- compliance assessment;
- recommendations;
- territorial assessment;
- Bolkestein assessment.

Required output metadata:

- rules applied;
- evidence identifiers;
- graph nodes used;
- score calculation;
- governance verdict;
- confidence;
- EVIDE record identifier.

## Phase 3 — Runtime replacement

Replace external provider calls in:

- `main.py`;
- `orchestrator.py`;
- `qen-bolkestein`.

No endpoint removal during the first compatibility stage.

## Phase 4 — Test refactor

Replace provider mocks and fallback tests with tests for:

- deterministic outputs;
- rule coverage;
- evidence provenance;
- graph traceability;
- EVIDE registration;
- invalid evidence rejection;
- reproducibility.

## Phase 5 — CI and deployment cleanup

Remove external AI secrets and SDK installation from:

- GitHub Actions;
- requirements files;
- runtime environment;
- systemd environment files.

## Phase 6 — API normalization

Deprecate provider-specific route names.

Temporary compatibility aliases may remain, but responses must identify:

`decision_authority: QEN_SOVEREIGN_ENGINE`

## Phase 7 — Verification

- unit tests;
- integration tests;
- health checks;
- endpoint compatibility checks;
- evidence-chain verification;
- repository scan for remaining decision-provider dependencies.
