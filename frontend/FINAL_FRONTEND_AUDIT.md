# KAIROS-TWIN Final Frontend Audit

Date: 2026-09-12

## Scope

This audit covers the existing React/TypeScript/Vite frontend under `frontend/src`, including routing, pages, shared demo state, API wrappers, types, loading/error/empty states, tests, and the backend API contracts needed for frontend integration.

The ML/backend foundation remains frozen:

- Production model: Random Forest
- Production artifact: `experiments/results/model_pipeline.pkl`
- Production threshold: `0.5`
- Calibration: `false`
- Feature contract: authoritative 46-feature order
- Pipeline: imputer -> scaler -> RandomForestClassifier
- XGBoost: benchmark/candidate only, not promoted

## Existing Architecture

- `App.tsx` defines the final routed application shell with `DemoProvider`, `Layout`, and pages for Command Center, Digital Twin, Risk, What-If, Agents, Faculty, and Recommendations.
- `DemoContext.tsx` is the central state owner for the demo workflow. It builds synthetic observation windows, calls backend endpoints, stores derived outputs, and clears downstream state when the selected student/input changes.
- `api/client.ts` and `api/endpoints.ts` provide the API layer with classified request failures.
- `types/index.ts` matches the current backend response shapes used by the frontend.
- `Layout`, `Sidebar`, `TopBar`, `DemoBanner`, and `DemoModal` provide the shared presentation shell.

## Pages And Components Reviewed

- Pages: `CommandCenter`, `DigitalTwin`, `RiskIntelligence`, `WhatIfLab`, `Recommendations`, `AgentControl`, `FacultyView`
- Components: `Sidebar`, `TopBar`, `DemoBanner`, `DemoModal`, `StudentInputPanel`
- Context/hooks: `DemoContext`, `useDemoStudent`, `useLiveIntegration`
- API/types/tests: `api/client`, `api/endpoints`, `types/index`, frontend Vitest suites
- Backend contracts checked where needed: `/health`, `/metadata/model`, `/states/compute`, `/predictions`, `/diagnostics`, `/simulations/run`, `/recommendations/generate`, `/interventions/log`, `/outcomes/{id}/followup`

## What Was Already Good

- The application already used a clear routed shell and a single shared `DemoContext`.
- Selection-version protection was already present in `DemoContext` and prevents stale async responses from replacing newer student state.
- API client errors are categorized into network/auth/not-found/server/invalid-request/unknown states.
- The frontend already used canonical intervention decisions in tests and endpoint types.
- The core pages already map to the final demo story: input -> twin -> prediction -> diagnostics -> what-if -> recommendation -> intervention.
- The backend model metadata and production serving contracts are available without needing frontend-side ML changes.

## Problems Found

- `Sidebar` displayed hardcoded green subsystem statuses, which could mislead a live review if the backend/model was unreachable.
- `TopBar` showed API health but did not surface production model metadata or threshold context.
- `WhatIfLab` kept local scenario results that could remain visible after a student/context switch or a late response.
- `Recommendations` rendered raw JSON snippets, which looked unfinished and was not professor-friendly.
- The primary intervention loop did not expose the canonical `ask_more` decision everywhere.
- Follow-up/outcome recording was not integrated into the primary demo flow.
- The Command Center pipeline status had seven grid columns while the workflow now has eight stages.
- `DigitalTwin` had a visible label typo in the input summary.
- `useLiveIntegration.ts` appears unused by the routed demo and contains legacy demo-shaped values. It was left untouched because it is not part of the active final path.

## Changes Implemented

- Removed fake subsystem health dots from `Sidebar`; live API/model status is now represented in the header.
- Extended `TopBar` to fetch `/metadata/model` after a healthy `/health` response and show production RF/threshold context when available.
- Added follow-up outcome state and `recordFollowup()` to `DemoContext` using the existing backend follow-up endpoint.
- Preserved and extended stale-state protection so recommendations, decisions, and follow-ups are cleared when student/twin context changes.
- Restricted follow-up outcome recording to accepted intervention decisions only.
- Added `ask_more` as a visible decision action in the Command Center.
- Added intervention/follow-up UI to the Command Center and Recommendations page.
- Replaced raw recommendation JSON display with structured backend fields: issue, suggested action, rationale, confidence, baseline risk, scenario projection, expected benefit, and caveats.
- Hardened `WhatIfLab` local scenario state against repeated requests, slow responses, and student switching.
- Fixed the Digital Twin input label typo.
- Added focused tests for follow-up endpoint usage and preventing follow-up recording for rejected decisions.

## API Contracts Verified

- `/health`: used for API/model availability.
- `/metadata/model`: used for production model name and threshold display.
- `/states/compute`: receives the current student synthetic observation window.
- `/predictions`: receives the computed twin state and returns estimated 7-day overload probability.
- `/diagnostics`: receives the computed twin state and returns agent diagnoses.
- `/simulations/run`: receives the computed twin state and selected scenarios.
- `/recommendations/generate`: receives the computed twin state and returns backend-generated recommendation fields.
- `/interventions/log`: uses canonical decisions only: `accepted`, `rejected`, `deferred`, `ask_more`.
- `/outcomes/{id}/followup`: used only after an accepted intervention decision.

## Real Vs Unavailable Data

- Real backend outputs are used for twin state, risk prediction, diagnostics, simulations, recommendations, intervention IDs, follow-up outcomes, health, and model metadata.
- Demo observations are synthetic and generated client-side from the selected preset/current input before being sent to the backend.
- No fake health indicators remain in the sidebar.
- No fake recommendation result is displayed; unavailable backend fields show unavailable/empty states instead of invented values.
- No local SHAP or personal explanation is claimed. The UI uses backend fields and cautious wording such as estimated risk, key signals, and scenario projection.

## Final Demo Flow

1. Open the Command Center.
2. Select a demo scenario or adjust the student input.
3. Click `2. COMPUTE TWIN`.
4. Click `PREDICT` to show estimated next-7-day overload risk.
5. Click `RUN` diagnostics to inspect actual agent diagnoses.
6. Click `RUN` What-If, or open What-If Lab for explicit scenario exploration.
7. Click `GENERATE` recommendation.
8. Record one of the canonical decisions: `accepted`, `rejected`, `deferred`, `ask_more`.
9. If accepted, record day+7 follow-up outcome through the backend follow-up endpoint.
10. Open Faculty View to inspect history/outcome context.

## Error, Loading, Empty, And Stale-State Handling

- API-driven primary actions show loading states and disable repeated submissions where needed.
- Classified API failures render visible error states rather than blank screens.
- Empty states tell the user what prerequisite step is needed.
- `DemoContext` clears downstream state after student/input changes.
- Async responses are guarded by selection version checks.
- `WhatIfLab` now ignores late responses from old student selections or repeated scenario runs.

## Verification

- `npm test -- --run`: 15 passed
- `npm run typecheck`: passed
- `npm run lint`: passed
- `npm run build`: passed
- `pytest -q`: 150 passed, 1 warning
- `pytest -q tests/test_production_serving.py`: 10 passed
- Production RF artifact SHA256: `3BAA73C949FAB3191EBE6F39F081C504F6E3B82ADAC0AA9EAB388CFEEB50AC36`

Build note: Vite reports a large JavaScript chunk warning after successful production build. This is not a build failure and was not changed during the final reliability pass.

## Remaining Known Limitations

- The final demo uses synthetic client-generated observations, not a live student data integration.
- Follow-up outcome recording uses a demo day+7 synthetic observation window derived from the current selected profile.
- `useLiveIntegration.ts` appears legacy/unused in the active routed demo and was left untouched to avoid unnecessary churn.
- The frontend does not add calibration, SHAP, new ML models, new agents, new databases, authentication, or deployment infrastructure.

## Final Status

Frontend reliability and presentation polish are complete for the frozen KAIROS-TWIN final demo path. The ML/backend foundation remains unchanged.
