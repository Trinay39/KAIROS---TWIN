# Recommendations And Interventions

## Recommendation Generation

Source files:

- `phase6_orchestrator.py`
- `agents/orchestrator_agent.py`
- `intervention/recommendation.py`
- `simulation/scenario_generator.py`
- `simulation/counterfactual_engine.py`
- `simulation/scenario_ranker.py`

The orchestrator workflow is:

1. Predict baseline overload risk.
2. Run specialized agents: Academic, Behavioral, Recovery, Workload, Schedule.
3. Generate candidate scenarios.
4. Simulate each scenario.
5. Rank scenarios.
6. Generate final recommendation through `LLMReasoner` or fallback mock mode.
7. Return a `Recommendation` with scenario details, risk estimates, changed features, diagnoses, confidence, and caveats.

## Personalization

Personalization is based on the current `StudentTwinState(t)` and agent diagnoses. Scenario generation thresholds inspect workload pressure, deadline density, sleep deficit, study consistency, stress, and confidence.

## Ranking And Priority

Ranking uses `ScenarioRanker`:

- Risk reduction weight: 0.60.
- Strain reduction weight: 0.25.
- Feasibility weight: 0.15.

This is transparent scoring, not a learned causal ranking.

## More Recommendations Behavior

The backend can generate multiple scenarios and ranked results through `/simulations/run`; the frontend can use the scenario explorer and "more" style flows by requesting generated/all scenarios and choosing additional ranked items. The final single recommendation endpoint returns the orchestrated recommendation payload.

## Deduplication

The core scenario generator can produce repeated scenario families under different triggers, especially recovery-focused scenarios that include sleep and workload reduction. No separate global deduplication module was found. Report text should avoid claiming advanced deduplication beyond deterministic generation and ranking.

## What-If Connection

Recommendations are grounded in counterfactual result fields:

- `baseline_risk`
- `counterfactual_risk`
- `risk_delta`
- `risk_reduction_percentage`
- `strain_delta`
- `changed_features_count`
- `top_changed_features`

## Canonical Intervention Decisions

The API and registry use these canonical response values:

- `accepted`
- `rejected`
- `deferred`
- `ask_more`

Source: `api/service.py`, `intervention/intervention_registry.py`.

## Intervention Logging

`/interventions/log` stores a recommendation in `InterventionRegistry`. The record includes intervention ID, student ID, scenario information, predicted baseline and counterfactual risk, predicted delta, status, offered day, response, feedback, outcome link, agent diagnoses, and confidence.

## Follow-Up And Outcome Tracking

Accepted interventions can start outcome tracking. `/outcomes/{id}/followup` validates follow-up observations, requires `followup_day = offered_at_day + 7`, recomputes a follow-up twin state, predicts follow-up risk, calculates actual risk delta, compares predicted and actual deltas, and stores an outcome report.

## Faculty View Connection

Faculty View consumes `/analytics/system` and `/students/{student_id}/history`. It displays registry totals, acceptance rate, follow-ups, success rate, current risk and state summaries, observation history, and intervention records.
