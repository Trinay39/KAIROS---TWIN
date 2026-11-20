# Testing And Verification

Verification was run against the current project state on 2026-09-16. No application source code, ML artifacts, feature contracts, or model files were modified for this evidence package.

## Backend

| Command | Result |
|---|---|
| `python -m pytest -q` | 154 passed, 1 warning |
| `python -m pytest -q tests/test_production_serving.py` | 10 passed |
| `python -m pytest -q tests/test_phase7_api.py` | 24 passed, 1 warning |
| `python -m pytest -q tests/test_phase8_adapter.py` | 4 passed, 1 warning |

Backend warning: `StarletteDeprecationWarning` from FastAPI/Starlette TestClient importing httpx compatibility.

## Frontend

| Command | Result |
|---|---|
| `npm test -- --run` | 30 passed |
| `npm run typecheck` | passed |
| `npm run lint` | passed |
| `npm run build` | passed |

Frontend test warning: Recharts emits zero-width/zero-height chart warnings under jsdom for `StudentHistory.test.tsx`.

Build warning: Vite reports that the generated JS chunk is larger than 500 kB after minification. Build still passed.

Build artifact summary:

- `../dist-frontend/index.html`: 0.69 kB, gzip 0.41 kB.
- `../dist-frontend/assets/index-CkcREx2A.css`: 19.09 kB, gzip 4.50 kB.
- `../dist-frontend/assets/index-CP7rqUTN.js`: 699.09 kB, gzip 190.29 kB.

## Artifact Hash Verification

Production artifact:

`experiments/results/model_pipeline.pkl`

SHA256:

`3BAA73C949FAB3191EBE6F39F081C504F6E3B82ADAC0AA9EAB388CFEEB50AC36`

## Model Metadata Verification

`Phase7Service().model_metadata()` reports:

- `model_name`: `rf`
- `model_type`: `RandomForestClassifier`
- `is_loaded`: true
- `num_features`: 46
- `threshold`: 0.5
- `threshold_source`: `fixed_default_for_served_rf_model`
- `calibrated`: false
- `artifact_type`: `kairos_twin_production_pipeline`
- `model_artifact`: `experiments/results/model_pipeline.pkl`
- `production_model_available`: true
- `retraining_available`: false

## Test Coverage Areas

- Unit tests for core components and feature contract.
- Production serving tests for preprocessing and feature-order integrity.
- Phase 7 API tests for request validation, auth-facing endpoints, and service behavior.
- Phase 8 adapter tests for safe observation normalization and disallowed mappings.
- Frontend tests for API client, endpoints, DemoContext, What-If UI, Faculty View, Student History, and scenario parser.

## Live Smoke Evidence

Previous local smoke verification confirmed the backend health endpoint reported model loaded and production model available. Current evidence package did not start or change application servers.
