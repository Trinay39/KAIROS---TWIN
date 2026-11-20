# KAIROS-TWIN Final QA Report

Date: 2026-09-15

## System Status

- Backend: PASS (`pytest -q` -> 150 passed, 1 warning)
- Frontend: PASS (`npm test -- --run` -> 19 passed)
- TypeScript: PASS (`npm run typecheck`)
- Lint: PASS (`npm run lint`)
- Build: PASS (`npm run build`)
- Production serving: PASS (`pytest -q tests/test_production_serving.py` -> 10 passed)
- ML: FROZEN Random Forest production model
- Production artifact: PASS, `experiments/results/model_pipeline.pkl`
- Production artifact SHA256: `3BAA73C949FAB3191EBE6F39F081C504F6E3B82ADAC0AA9EAB388CFEEB50AC36`

Build note: Vite still reports a large JavaScript chunk warning after a successful build. This is not a build failure.

## End-to-End Flow

- Open Command Center: PASS
- Select/create demo student context: PASS
- Submit/adjust student observations: PASS
- Compute Digital Twin: PASS
- Verify Twin state appears: PASS
- Generate prediction: PASS
- Verify overload probability appears: PASS
- Verify risk category appears: PASS
- Run diagnostics: PASS
- Verify diagnostics correspond to selected student/state: PASS
- Run What-If scenario: PASS
- Verify scenario result belongs to current student/state: PASS
- Generate recommendation: PASS
- Verify recommendation corresponds to current state: PASS
- Select `accepted`: PASS
- Select `rejected`: PASS
- Select `deferred`: PASS
- Select `ask_more`: PASS
- Verify intervention is logged: PASS
- Verify accepted follow-up/outcome can be recorded: PASS
- Open Faculty View: PASS
- Verify history/outcome information is available: PASS

Live backend smoke result:

- Student: `STU_QA_A`
- Twin day: `50`
- Prediction probability: `0.4396971114368916`
- Diagnostics total: `7`
- Simulation results: `1`
- Recommendation student: `STU_QA_A`
- Accepted intervention ID: `STU_QA_A_50_1789463806.131961`
- Rejected/deferred/ask_more responses persisted with canonical values
- Follow-up outcome ID: `outcome_STU_QA_A_50_1789463806.131961`
- History interventions after smoke: `4`
- Analytics interventions after smoke: `4`

## Edge Cases

- Probability low-edge smoke: PASS, probability `0.2358472834521855`, in range `[0, 1]`
- Probability high-edge smoke: PASS, probability `0.43077765191267103`, in range `[0, 1]`
- Stress boundary values `0` and `10`: PASS through live prediction smoke
- Empty/partial display states: PASS through focused frontend tests and source review
- Null/optional backend fields: PASS through existing guarded rendering and tests
- Invalid What-If numeric parameters: FIXED, client now blocks invalid/NaN scenario requests
- No NaN/Infinity display paths found in final demo-critical pages

## API Failure Handling

- Network failure: PASS, frontend API client returns safe backend-unavailable message
- Auth/config failure `403`: PASS, safe access-configuration message
- Validation failure `400` / `422`: PASS, safe validation message
- Server failure `500`: PASS, safe service-unavailable message
- Malformed JSON response: FIXED, now wrapped as a safe `ApiError`
- Raw Python stack traces are not exposed through frontend user messages

## Student Switching

PASS.

- `DemoContext` preserves selection-version protection.
- Student changes clear twin, prediction, diagnostics, What-If, recommendation, intervention, decision, and follow-up state.
- Late async responses are ignored when they no longer match the current student/day selection.
- Faculty View now tags loaded history to the selected student so stale history/errors do not appear under a new student.

## Intervention Flow

PASS.

- Canonical decisions remain exactly: `accepted`, `rejected`, `deferred`, `ask_more`.
- Endpoint payload uses the backend shape for `/interventions/log`.
- UI prevents duplicate decision logging after a decision has been persisted.
- UI prevents duplicate follow-up submission after an outcome has been recorded.
- Follow-up/outcome recording is available only for accepted intervention decisions.
- Non-accepted decisions do not create accepted follow-up outcomes in the frontend.

## Browser/UI

PASS with limitation.

- In-app browser automation was unavailable in this session (`agent.browsers.list()` returned `[]`).
- Frontend dev server route smoke passed for:
  - `/`
  - `/twin`
  - `/risk`
  - `/whatif`
  - `/agents`
  - `/faculty`
  - `/recommend`
- All routes returned HTTP 200 and the SPA root.
- Source-level responsive review found no new horizontal-overflow or clipped-modal risk introduced by this QA pass.

## Tests

- `npm test -- --run`: 4 files passed, 19 tests passed
- `npm run typecheck`: passed
- `npm run lint`: passed
- `npm run build`: passed
- `pytest -q`: 150 passed, 1 warning
- `pytest -q tests/test_production_serving.py`: 10 passed

## Production Artifact

PASS.

- Artifact path: `experiments/results/model_pipeline.pkl`
- SHA256: `3BAA73C949FAB3191EBE6F39F081C504F6E3B82ADAC0AA9EAB388CFEEB50AC36`
- The artifact hash matches the frozen expected value.
- No ML model, threshold, calibration, feature contract, training code, or backend architecture was changed.

## Bugs Fixed

- Faculty View now loads real backend student history and system analytics instead of only describing the view.
- Faculty View avoids stale history/error display after student switching.
- What-If Lab now blocks invalid/NaN numeric scenario parameters before calling the backend.
- What-If Lab labels the actual `/simulations/run` endpoint instead of stale `/simulate` text.
- Risk Intelligence now renders classified prediction failure states.
- Agent Control now renders all classified diagnostics failure states, not only generic errors.
- Command Center and Recommendations now disable persisted decision/follow-up buttons to reduce duplicate demo submissions.
- API client now handles malformed JSON responses with a safe user-facing error.
- `frontend/FINAL_FRONTEND_AUDIT.md` endpoint names were corrected to match frozen backend routes.

## Remaining Known Limitations

- The final demo uses synthetic observations, not live student telemetry.
- Follow-up outcome recording uses a synthetic day+7 observation window derived from the selected demo profile.
- In-app browser visual automation was not available in this session, so visual QA was route/source based rather than screenshot based.
- Vite reports a large production JS chunk warning after successful build.
- `useLiveIntegration.ts` remains legacy/unused in the active routed demo and was left untouched to avoid unnecessary churn.

## Final Status

PASS.

KAIROS-TWIN is ready for the final frozen demo path. Critical demo reliability issues found during this QA pass were fixed, the complete backend contract smoke test passed, all required automated checks passed, and the production Random Forest artifact remains unchanged.
