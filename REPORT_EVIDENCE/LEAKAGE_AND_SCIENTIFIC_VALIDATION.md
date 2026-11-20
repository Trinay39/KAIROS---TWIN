# Leakage And Scientific Validation

## Feature Leakage Safeguards

- `core/twin_engine.py` filters observations to `student_df[day <= t]`.
- `core/feature_engine.py` extracts features from `StudentTwinState(t)` only.
- `core/label_engine.py` computes labels from `[t+1, t+7]` only.
- `api/service.py` rejects future observations where `obs_day > requested day`.
- `api/service.py` rejects future label fields: `y_binary`, `y_continuous`, `split`, `outcome_window`, `future_label`, and keys starting with `c_` or `y_`.
- `simulation/counterfactual_engine.py` clones the baseline state before applying scenario changes and asserts the baseline was not modified.

## Temporal Validation

Source: `core/temporal_sampler.py`.

The temporal split separates prediction days:

- Train: days 15-55.
- Validation: days 56-69.
- Test: days 70-83.
- Outcome-only: days 84-90.

The sampler includes checks for no train/validation/test day overlap and proper ordering.

## Student Generalization

`TemporalSampler.create_student_level_split` implements a secondary student-level 80/10/10 split using seed 42. This is separate from the primary temporal evaluation.

## Constant And Unavailable Features

The twin-integrity work investigated features that were constant or unavailable in the original synthetic observation schema. The current implementation preserves the frozen 46-feature contract while marking unavailable values through provenance/defaults. Examples include break rate, distraction rate, focus quality, procrastination index, confidence, and assignment effort fields. This is a prototype limitation, not a hidden model feature.

## Provenance

`TwinEngine._build_provenance` records field-level provenance with:

- `type`: observed, derived, predicted, or imputed default.
- `source`: raw field or service.
- `window`: current day, 7d, 14d, 30d, etc.
- `unit`.
- `formula_id`.
- `imputed` flag.

This supports the distinction between observed, derived, predicted, and scenario-projected values.

## Reproducibility

- Simulator seed: 42.
- Temporal sampler seed for student-level split: 42.
- Production feature order is hardcoded and tested.
- Preprocessing metadata records `fit_scope=train_split_only`.
- Production artifact hash: `3BAA73C949FAB3191EBE6F39F081C504F6E3B82ADAC0AA9EAB388CFEEB50AC36`.

## Artifact Integrity

The production service reports:

- `model_artifact`: `experiments/results/model_pipeline.pkl`.
- `model_type`: `RandomForestClassifier`.
- `num_features`: 46.
- `threshold`: 0.5.
- `calibrated`: false.

`simulation/prediction_service.py` validates that the loaded artifact feature order matches `FeatureEngine.FEATURE_NAMES`.

## Interpretation Boundary

The model prediction is an estimate, not a guarantee. It is trained on synthetic data and predicts an overload label defined by the project. What-if scenarios modify state variables and re-run the same model; they are scenario projections, not causal inference.

## Data Type Distinctions

- Observed: direct input measurements such as study hours, sleep hours, stress, grade, attendance, workload pressure, and event flags.
- Derived: rolling or transformed state values such as attendance trend, sleep deficit, study consistency, recovery ratio, and academic load.
- Predicted: model outputs such as overload probability and binary label at threshold.
- Scenario-projected: counterfactual estimates after a simulated change to a cloned state.
