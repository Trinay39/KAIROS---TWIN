# Project Overview

## Project Title

KAIROS-TWIN: Student Digital Twin for Academic Overload Risk, What-If Simulation, and Intervention Tracking.

## Objective

The project estimates short-term academic overload risk for a student from longitudinal observations, represents the student's current condition as a digital twin, explores hypothetical interventions, and logs follow-up outcomes. The implementation connects a synthetic longitudinal dataset, a temporal label definition, a 46-feature production contract, a frozen production ML model, a FastAPI backend, and a React frontend.

## Problem Statement

Academic overload is not represented by one signal alone. The project models overload as a future 7-day outcome using missed deadlines, grade deterioration, study collapse, recovery failure, and high stress. The system must predict risk from observations available at or before the current day, explain state factors, test simulated scenario changes, and support intervention follow-up without leaking future outcomes into features.

## Motivation

Students and faculty need earlier, interpretable warnings about workload and recovery pressure. The system is designed to show risk estimates, the underlying twin state, counterfactual scenario projections, and follow-up tracking in one workflow instead of producing only an isolated classifier output.

## Novelty And Contribution

- A digital twin representation, `StudentTwinState`, built from historical observations through `core/twin_engine.py`.
- A temporally valid label engine in `core/label_engine.py` using future `[t+1, t+7]` outcomes only for labels.
- A frozen 46-feature production feature contract in `core/feature_engine.py`.
- Production serving through `simulation/prediction_service.py` with artifact feature-order validation.
- What-if simulation through `simulation/counterfactual_engine.py` and transparent ranking through `simulation/scenario_ranker.py`.
- Recommendation and intervention logging through `phase6_orchestrator.py`, `intervention/intervention_registry.py`, and `intervention/outcome_tracker.py`.
- A frontend demo workflow covering command center, twin, risk, what-if lab, recommendations, faculty view, and student history.

## Target Users

- Students reviewing current overload risk and potential routine changes.
- Faculty or advisors monitoring risk, history, and intervention outcomes.
- Project evaluators reviewing a reproducible academic prototype.

## Main Use Cases

- Compute a student's current digital twin from observations.
- Estimate overload probability using the frozen production model.
- Inspect diagnostics from specialized academic, behavioral, recovery, workload, and schedule agents.
- Generate or enter what-if scenarios.
- Compare baseline risk against counterfactual risk.
- Generate a recommendation, log the student's response, and track follow-up outcome.
- View student history charts and faculty-level intervention analytics.

## Major Capabilities

- Synthetic longitudinal data simulation: `student_simulator.py`.
- Temporal sampling: `core/temporal_sampler.py`.
- Label generation: `core/label_engine.py`.
- Twin state computation: `core/twin_engine.py`.
- Feature extraction: `core/feature_engine.py`.
- Production prediction: `simulation/prediction_service.py`.
- Scenario generation/simulation/ranking: `simulation/scenario_generator.py`, `simulation/counterfactual_engine.py`, `simulation/scenario_ranker.py`.
- Recommendation and intervention workflow: `phase6_orchestrator.py`, `intervention/*`.
- API service: `api/main.py`, `api/service.py`, `api/schemas.py`.
- Frontend UI: `frontend/src`.

## End-To-End Workflow

1. A user selects or enters a student and day in the frontend.
2. The frontend sends observations to `/states/compute`.
3. `Phase7Service` validates observations, rejects future labels, adapts safe field names/scales, and calls `TwinEngine`.
4. `TwinEngine` filters to observations where `day <= t` and computes `StudentTwinState(t)`.
5. `FeatureEngine` extracts the frozen 46-feature vector.
6. `PredictionService` loads `experiments/results/model_pipeline.pkl`, verifies feature order, applies preprocessing, and returns overload probability at threshold `0.5`.
7. Diagnostics run specialized agents over the twin state.
8. Scenario tools generate or accept user scenarios, modify a cloned twin state, recompute features, and compare baseline versus counterfactual model estimates.
9. The orchestrator ranks scenario results and produces a recommendation with caveats.
10. Interventions are logged, student responses are recorded, and accepted interventions can be followed up after 7 days.
11. History and Faculty View display observations, intervention records, outcomes, and aggregate analytics.
