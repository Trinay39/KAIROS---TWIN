# What-If And Scenarios

## Core Definitions

Baseline risk is the model estimate for the current `StudentTwinState(t)`.

Counterfactual risk is the model estimate after selected state variables are changed in a simulated scenario and the 46-feature vector is recomputed.

These are model-estimated scenario projections. They are not causal inference.

## Backend Scenario System

Source files:

- `simulation/scenario_schema.py`
- `simulation/scenario_generator.py`
- `simulation/state_modifier.py`
- `simulation/counterfactual_engine.py`
- `simulation/scenario_ranker.py`
- API endpoint `/simulations/run`

## Supported Scenario Types

- `move_assignment`
- `remove_assignment`
- `reduce_workload`
- `increase_study_time`
- `increase_sleep`
- `reduce_deadline_density`

API payloads may use enum names such as `INCREASE_SLEEP` or enum values such as `increase_sleep`; `api/service.py` normalizes both.

## Scenario Generation Rules

`ScenarioGenerator` uses deterministic rules:

- Workload pressure > 0.7 -> workload reductions of 10%, 20%, and 30%.
- Deadline density trend > 0.6 -> deadline redistribution.
- Sleep deficit > 2.0 hours -> sleep targets 7.5, 8.0, and 8.5 hours.
- Study consistency < 0.4 -> study increases of 1, 2, and 3 hours/day for 7 days.
- Stress > 3.4 and confidence < 2.5 -> recovery-focused scenarios.

`include_all=true` asks the generator to include all possible scenario families rather than only triggered ones.

## Counterfactual Engine

`CounterfactualEngine.simulate` performs:

1. Predict baseline from original state.
2. Clone baseline state.
3. Apply scenario modification to cloned state.
4. Recompute all 46 features.
5. Predict counterfactual risk.
6. Compute `risk_delta = counterfactual - baseline`.
7. Compute `risk_reduction_percentage = (baseline - counterfactual) / baseline * 100`.

The engine checks that the baseline state remains unchanged.

## Ranking Methodology

`ScenarioRanker` computes:

`score = 0.60 * normalized_risk_reduction + 0.25 * normalized_strain_reduction + 0.15 * feasibility_score`.

Weights are design parameters, not learned causal weights. Feasibility is adjusted by whether a scenario requires instructor approval, instructor coordination, student action, risk level, and sustainability.

## Scenario Explorer And Natural-Language Parser

Source: `frontend/src/utils/scenarioIntent.ts`.

Preset explorer intents:

- `sleep_more`
- `study_less`
- `reduce_stress`
- `improve_recovery`
- `improve_study_consistency`
- `reduce_deadline_pressure`
- `reduce_workload`

The natural-language parser supports examples such as:

- "sleep 1 hour more"
- "sleep to 8 hours"
- "study 30 minutes less"
- "study more"
- "reduce workload"
- "increase workload"
- "reduce stress"
- "improve recovery"
- "improve study consistency"
- "reduce deadline pressure"

Ambiguous or unsupported text returns `null` and the UI help text: `Please clarify the routine change. Try: sleep 1 hour more and study 30 minutes less.`

## Scientific Limitation

Changing a state variable in a cloned twin is not equivalent to proving that the same real-world intervention will cause that risk reduction. The result is a model-estimated projection under the project's learned/synthetic distribution and feature contract.
