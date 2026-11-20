# API Documentation

Source: `api/main.py`, `api/schemas.py`, `api/service.py`.

## Authentication

`/health` is public. All other listed endpoints require the API key dependency from `api/security.py`. Do not expose the actual `KAIROS_TWIN_API_KEY` value in the report.

The API uses strict Pydantic schemas with `extra="forbid"`.

## GET `/health`

Purpose: service health and production model availability.

Request: no body.

Response fields include `status`, `phase`, `prototype`, `model_loaded`, `production_model_available`, `calibrated`, `persistence_base`, `timestamp`.

## GET `/metadata/model`

Purpose: model metadata.

Request: no body.

Response fields include model name/type, load status, feature order, threshold, calibration, artifact type, probability source, artifact path, production availability, and retraining availability.

## POST `/states/compute`

Purpose: compute `StudentTwinState`.

Request: `ComputeStateRequest`:

- `student_id`: string.
- `day`: integer 1-90.
- `observations`: non-empty list of observation dictionaries.
- `data_source`: string, default `synthetic`.

Important validation: observations must include the requested day, must not include day greater than requested day, and must not include future labels or outcome windows.

Response: serialized `StudentTwinState` with raw latest values, academic, behavioral, recovery, workload, engagement, temporal, prediction, history, and provenance sections.

## POST `/predictions`

Purpose: predict overload risk for a provided twin state.

Request: `StateRequest`:

- `twin_state`: `StudentTwinStateModel`.
- `day`: integer 1-90.

Response: prediction snapshot from `PredictionService`, including overload probability, threshold, label, feature importances/confidence where available.

## POST `/diagnostics`

Purpose: run specialized agent diagnostics.

Request: `StateRequest`.

Response fields:

- `student_id`
- `day`
- `diagnoses`: by agent, with `issue_name`, `severity`, `description`, `affected_fields`, `suggested_scenario_types`, `confidence`
- `statistics`: aggregate diagnostic counts and top issues

## POST `/scenarios/generate`

Purpose: generate candidate scenarios.

Request: `GenerateScenariosRequest`, same as `StateRequest` plus `include_all`.

Response fields:

- `student_id`
- `day`
- `scenarios`: scenario dictionaries with ID, type, description, parameters, affected variables, feasibility metadata, explanation, created time

## POST `/simulations/run`

Purpose: run what-if simulations.

Request: `SimulationRequest`, same as `StateRequest` plus:

- `scenarios`: optional list of `ScenarioPayload`
- `include_all_if_empty`: boolean

Scenario payload fields:

- `scenario_id`
- `scenario_type`
- `description`
- `parameters`
- `affected_state_variables`
- `feasibility_metadata`
- `human_readable_explanation`

Response fields:

- `student_id`
- `day`
- `results`: baseline/counterfactual probabilities, risk deltas, strain fields, changed feature counts, interpretation
- `ranked_scenarios`: rank, score components, baseline risk, counterfactual risk, estimated risk reduction

## POST `/recommendations/generate`

Purpose: generate one orchestrated recommendation.

Request: `RecommendationRequest`, same as `StateRequest`.

Response: `RecommendationPayload` with scenario details, baseline risk, counterfactual risk, risk delta, risk reduction percentage, strain delta, changed features, explanation, diagnoses, confidence, caveats, timestamp, student ID, and day.

## POST `/interventions/log`

Purpose: log a recommendation and optional student response.

Request: `LogInterventionRequest`:

- `recommendation`: `RecommendationPayload`
- `student_response`: optional canonical response
- `feedback`: optional text

Response fields:

- `intervention_id`
- `record`
- `persistence_base`

## PATCH `/interventions/{intervention_id}/response`

Purpose: update student response.

Request: `UpdateResponseRequest`:

- `response`: one of `accepted`, `rejected`, `deferred`, `ask_more`
- `day`: integer 1-90
- `feedback`: optional text

Response fields:

- `intervention_id`
- `record`

## POST `/outcomes/{intervention_id}/followup`

Purpose: record follow-up outcome.

Request: `FollowupOutcomeRequest`:

- `followup_day`: integer 1-90
- `observations`: non-empty observation list
- `student_feedback`: optional
- `student_feedback_text`: optional

Validation: follow-up day must equal `offered_at_day + 7`.

Response fields:

- `outcome_id`
- `report`
- `record`

## GET `/students/{student_id}/history`

Purpose: student intervention and observation history.

Query:

- `day`: optional integer.

Response includes intervention history, outcome history, acceptance/completion/success rates, and, when a demo day is selected, deterministic observations plus `observation_summary`.

## GET `/analytics/system`

Purpose: faculty/system analytics.

Response includes registry totals, acceptance rate, completion rate, effectiveness, scenario-type stats, outcome totals, success rate, prediction accuracy stats, and supported scenarios by agent.
