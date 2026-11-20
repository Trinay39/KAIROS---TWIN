# KAIROS-TWIN Phase 7 API

Phase 7 is an additive FastAPI research prototype layer over the frozen Phase
2-6 implementation. It exposes state construction, prediction, simulation,
recommendation, intervention logging, follow-up tracking, and analytics without
retraining models or changing the scientific implementation.

## Baseline

- Frozen Phase 6 baseline: 91/91 tests passing.
- Phase 7 persistence is isolated under `data/phase7/`.
- Overload probabilities come only from the existing RF `PredictionService`.
- API endpoints do not accept model paths, pickle paths, import paths, or
  arbitrary filesystem paths.

## Run

From the project root, put the same local development key in `.env` as in
`frontend/.env.local`:

```text
KAIROS_TWIN_API_KEY=your-local-dev-key
```

The backend reads this setting automatically. An environment variable named
`KAIROS_TWIN_API_KEY` takes precedence over the `.env` value.

Start the backend in PowerShell:

```bash
python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

Then start the frontend in a second terminal:

```bash
cd frontend
npm run dev
```

## Authentication

`GET /health` is public. All other endpoints require:

```http
Authorization: Bearer $KAIROS_TWIN_API_KEY
```

CORS is restricted to localhost and 127.0.0.1 origins for development.

## Endpoints

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| GET | `/health` | Service/model/persistence health | No |
| GET | `/metadata/model` | RF model metadata | Yes |
| POST | `/states/compute` | Compute `StudentTwinState(t)` using `TwinEngine` | Yes |
| POST | `/predictions` | Predict overload risk from `StudentTwinState` | Yes |
| POST | `/diagnostics` | Run Phase 6 specialized agent diagnostics | Yes |
| POST | `/scenarios/generate` | Generate Phase 5 candidate scenarios | Yes |
| POST | `/simulations/run` | Simulate and rank scenarios | Yes |
| POST | `/recommendations/generate` | Delegate to Phase 6 orchestration | Yes |
| POST | `/interventions/log` | Persist an offered intervention | Yes |
| PATCH | `/interventions/{intervention_id}/response` | Record student response | Yes |
| POST | `/outcomes/{intervention_id}/followup` | Compute independent day+7 state and track outcome | Yes |
| GET | `/students/{student_id}/history` | Student intervention/outcome history | Yes |
| GET | `/analytics/system` | System-level prototype analytics | Yes |

## Temporal Safety

The API boundary enforces:

- request `day` must equal `twin_state.day`;
- observations sent to `/states/compute` or follow-up tracking cannot include
  `day > t`;
- observations must include the requested day;
- `twin_state.temporal.day_of_semester` cannot exceed the requested day;
- scenario date constraints are delegated to Phase 5 scenario factories and the
  `CounterfactualEngine`;
- follow-up tracking computes a fresh day+7 state from observations using
  `TwinEngine`;
- future labels and outcome-window columns are rejected.

## Persistence

Phase 7 uses single-process JSON persistence with an in-process lock:

- `data/phase7/intervention_registry.json`
- `data/phase7/outcome_tracker.json`
- `data/phase7/request_audit.jsonl` reserved for future non-sensitive audit use

This is not a production database. It is intentionally scoped to the research
prototype.

