# QEN Sovereign Intelligence — Risk Assessment

## High risks

### Runtime regression

Removing provider calls without compatibility layers may break the Copilot,
wizard and existing clients.

Mitigation: contract capture, compatibility aliases and staged replacement.

### Semantic regression

Provider-generated free text may currently conceal missing deterministic
rules.

Mitigation: explicit rule inventory and governed recommendation templates.

### CI instability

Current tests assume provider clients, keys and fallback behaviour.

Mitigation: refactor tests before removing dependencies.

### Deployment failure

The deployment workflow injects provider secrets and installs provider SDKs.

Mitigation: modify CI only after the sovereign runtime passes locally.

## Medium risks

- outdated documentation;
- provider-specific endpoint names;
- stale environment variables;
- unused runtime packages;
- untracked historical assumptions.

## Governance risk

A merely cosmetic removal of provider names would not establish sovereignty.

Sovereignty requires deterministic authority, traceable evidence,
reproducible calculations and EVIDE registration.
