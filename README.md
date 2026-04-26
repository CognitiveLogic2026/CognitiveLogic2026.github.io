# Cognitive Logic — AI Governance Infrastructure

Cognitive Logic is an independent observatory designing computable ethics
infrastructure for AI systems operating under EU regulatory frameworks
(EU AI Act, GDPR, DSA).

It produces semantic knowledge graphs, ethical scoring engines, and
dual-brain AI architectures that make compliance structural rather than
declarative.

-----

## Core Architecture Layers

- **QEN Framework — Quantifiable Ethical Nodes**
  Semantic graph + numerical ethics scoring for institutions, restaurants,
  and hotels. Formula: `QEN = (Vs × 0.40) + (Va × 0.35) + (Vt × 0.25)`
- **Dual-Brain AI Engine**
  Claude (Anthropic) for EU AI Act classification and GDPR risk analysis.
  Gemini for QEN scoring and market intelligence.
  Orchestrated in parallel via `/full-analysis`.
- **Semantic Knowledge Graph**
  Static JSON graph — 21 nodes · 34 relations (v4).
  Node types: institutions, algorithms, regulations, KPIs, territories.
- **Regulatory Compliance Engine**
  EU AI Act Annex I / II / III classification.
  GDPR Art. 22 (automated decisions) and Art. 35 (DPIA) mapping.
- **Digital Identity & DID Infrastructure**
  `did:web:cognitivelogic.it:robertomalini`
  Decentralized identifier anchored on sovereign data node.
- **Fuorimenu — Editorial Observatory**
  Public-facing analytical layer. Translates technical findings into
  discourse on food ethics, institutional accountability, and AI policy.

-----

## Active Repositories

|Repository          |Description                                |Status|
|--------------------|-------------------------------------------|------|
|`CognitiveLogic2026`|Main API backend — Flask + Claude + Gemini |🟢 Live|
|`qen-framework`     |QEN Framework — graph, scoring, copilot UI |🟢 Live|
|`cognitivelogic-web`|Frontend — GitHub Pages · cognitivelogic.it|🟢 Live|

-----

## Infrastructure

```
Hetzner CAX21 ARM64 — Ubuntu 24.04 — 178.104.190.107

Nginx (443) → api.cognitivelogic.it
  ├── Flask :5000  — Claude API  (risk, compliance, analyze)
  ├── Flask :5001  — Gemini API  (qen-score, market-scan)
  └── orchestrator.py → /full-analysis (parallel dual-brain)
```

Deploy: GitHub Actions → Hetzner on push to `main`
DNS: SiteGround DNS Zone

-----

## System Philosophy

> Beyond interfaces, data must be intelligible, transparent, verifiable,
> and immediately operational for autonomous AI agents.

Cognitive Logic is grounded in a single principle: **ethics is not a
narrative. It is a dataset.**

Verifiability is a design principle, not a reporting activity.
The QEN scoring formula is public. The weights are documented.
The methodology is open to challenge.

-----

## Strategic Vision

Cognitive Logic aims to be a **reference architecture for computable
ethics in EU-regulated AI systems**, integrating:

- symbolic and semantic reasoning
- sustainability and ESG analytics
- EU AI Act structural compliance
- digital trust and decentralized identity
- dual-brain AI orchestration

into a single scalable governance framework.

**Target domains:** AI governance · HoReCa & food sector · Smart cities ·
ESG measurement · Autonomous multi-agent systems · Research & education

**Roadmap:**

- Q2 2026 — QEN Badge freemium · 10 pilot structures · Bando ER
- Q3 2026 — ETL open.er.it · CNA Bologna · 5 Pro clients
- Q4 2026 — Bologna 100 Botteghe · B2G dashboard · White label
- Q1 2027 — ETL TelemacoPay · Enterprise CCIAA · 2000+ nodes

-----

## Founder & Architect

**Roberto Bob Malini**
AI Ethics Architect — Founder @ Cognitive Logic
Bologna, Italy — 2026

`did:web:cognitivelogic.it:robertomalini`

-----

## Links

- Website: [cognitivelogic.it](https://cognitivelogic.it)
- API: [api.cognitivelogic.it](https://api.cognitivelogic.it)
- Copilot: [api.cognitivelogic.it/copilot](https://api.cognitivelogic.it/copilot)
- Editorial: [fuorimenu.substack.com](https://fuorimenu.substack.com)
- LinkedIn: [linkedin.com/in/robertobobmalini](https://linkedin.com/in/robertobobmalini)

-----

*© Cognitive Logic — Knowledge Infrastructure for Human & Artificial Intelligence*
