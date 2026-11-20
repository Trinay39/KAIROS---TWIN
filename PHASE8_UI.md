# Phase 8 — UI / Frontend

Status: completed · build passes · backend frozen at 110/110

## Scope
Polished React 18 + TypeScript + Vite + Tailwind v3 + Recharts + Framer Motion frontend over frozen Phase 7 REST API. 6 pages. Demo / synthetic-data mode only.

## Security / Auth preserved
- No hardcoded secrets in source. `VITE_KAIROS_TWIN_API_KEY` read from `import.meta.env` (env-only); `.env` not checked in; `.env.example` placeholders only.
- `ANTHROPIC_API_KEY` / `KAIROS_TWIN_API_KEY` never exposed in source.
- API client (`api/client.ts`): key from env or empty (dev mode); Authorization header optional.

## Synthetic-data disclaimers (all pages)
Every page carries explicit synthetic-data / research-prototype disclaimers (not clinical, not real-world predictions, model-estimated). No clinical intervention recommendations made.

## Pages (6)
- `/` — CommandCenter
- `/twin` — DigitalTwin (radar chart, state breakdown)
- `/risk` — RiskIntelligence (contributors, model info, 74% risk)
- `/whatif` — WhatIfLab (intervention toggles, scenario comparison)
- `/agents` — AgentControl (agent cards, load, status)
- `/faculty` — FacultyView (cohort chart, aggregate stats)

## Demo mode
DemoModal + TopBar: 4 synthetic scenarios (stable, deadline overload, recovery collapse, emerging overload). `useDemoStudent` hook connects to demo state.

## Build
`npm run build` → `dist-frontend/` (9.7s, 2323 modules). TypeScript clean; no `tsc` errors after `vite-env.d.ts`, missing type exports, and unused imports fixed.

## Tests
- Backend: 110/110 pass (`tests/test_phase6.py` + `tests/test_phase7_api.py` + rest of suite).
- Frontend: build passes; no separate test suite configured (UI-demo only, no scientific changes).

## Not changed
- Phase 2–7 frozen (orchestrator, ranker, schemas, tests untouched except pre-existing Phase 7 fix already applied).
- No Phase 9.
