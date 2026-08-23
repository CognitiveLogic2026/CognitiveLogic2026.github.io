# ADR-CLE-004 — QEN Sovereign Intelligence Principle

Status: APPROVED  
Date: 2026-07-23

## Decision

Cognitive Logic shall operate as a sovereign intelligence architecture.

Authoritative decisions shall derive exclusively from:

- Knowledge Graph;
- QEN Rule Engine;
- Governance Engine;
- EVIDE;
- proprietary algorithms;
- governed and verifiable evidence;
- intelligible data.

External AI providers shall not act as decision authorities.

## Consequences

External provider SDKs, secrets, calls, fallback mechanisms and
provider-dependent tests must be removed from authoritative runtime paths.

Public API compatibility may be temporarily preserved through governed
compatibility routes, but provider-specific naming must be deprecated.

External factual services may remain only as governed evidence sources,
subject to provenance, validation, traceability and deterministic handling.

## Governance constraint

No implementation is authorized by this document alone.

Implementation requires:

1. approved migration plan;
2. runtime backup;
3. compatibility assessment;
4. controlled change set;
5. test refactor;
6. deployment verification;
7. rollback evidence.
