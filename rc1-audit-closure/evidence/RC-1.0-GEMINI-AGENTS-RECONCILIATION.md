# Cognitive Logic — RC 1.0 Gemini & Agents Reconciliation

Date: 2026-08-01T00:45:37+02:00
Commit: 040baad109c6952a46ef980a6f8a8050b2e3e3c2
Branch: main

## Baseline

Gemini references: 172

Agents routes: 26

Provider references: 528

## Next implementation

- Deprecate public Gemini namespace.
- Preserve compatibility endpoints.
- Classify every /agents endpoint.
- Remove remaining provider branding.
- Keep full backward compatibility for RC 1.0.

Status: READY FOR IMPLEMENTATION

## Phase 3C — Legacy Gemini namespace deprecation

Verified implementation:

- The `/gemini/*` namespace remains available for backward compatibility.
- All `/gemini/*` responses now include `Deprecation: true`.
- All `/gemini/*` responses identify `/copilot-analyze` as the successor endpoint.
- All `/gemini/*` responses include `X-QEN-Compatibility-Route: legacy-gemini`.
- The deprecation applies to success and error responses.
- Non-Gemini routes are not marked as legacy compatibility routes.
- Dedicated deprecation tests passed.
- Complete automated test suite result: 55 passed, 1 non-blocking dependency warning.

Deferred:

- Removal of the `/gemini/*` namespace in a future approved release.
- Reconciliation and classification of all `/agents/*` endpoints.
- Renaming of provider-specific compatibility endpoint names.
- Current documentation and Nginx comments alignment.

## Phase 3D — Provider-named Agents compatibility routes

Verified implementation:

- `/agents/mistral-compliance` remains available as a backward-compatible route.
- Its successor is `/agents/compliance-auditor`.
- `/agents/mistral-advisor` remains available as a backward-compatible route.
- Its successor is `/agents/advisory-council`.
- Both compatibility routes include `Deprecation: true`.
- Both compatibility routes include `X-QEN-Compatibility-Route: legacy-provider-agent`.
- Sovereign agent routes are not marked as legacy.
- Dedicated compatibility-route tests passed.
- Complete automated test suite result: 58 passed, 1 non-blocking dependency warning.

Endpoint classification:

- Sovereign: compliance-auditor, territorial-mapper, advisory-council, bolkestein-assessment, score-businesses, places-batch-qen.
- Data service: intelligence-feed.
- External discovery utility: places-discovery.
- Legacy compatibility: mistral-compliance, mistral-advisor.

Deferred:

- Removal of provider-named route aliases in a future approved release.
- Alignment of AI Engine, LLM Index, privacy pages and runtime documentation.
- Removal of residual provider dependency declarations after source verification.
