# ML Experiments And Results

## Models Evaluated

Source files: `experiments/results/*`, `experiments/twin_integrity_fix/results/*`.

- Logistic Regression.
- Random Forest.
- XGBoost.

## Split And Reproducibility

- Random seed: 42.
- Temporal split: train days 15-55, validation days 56-69, test days 70-83.
- Warm-up days 1-14 are not prediction samples.
- Days 84-90 are outcome-only for label construction.
- Secondary student-level split is implemented in `core/temporal_sampler.py` with 80/10/10 students.
- Preprocessing: `SimpleImputer(strategy=mean)` and `StandardScaler`, fit on train split only.

## Production Model

The served production model is Random Forest:

- Artifact: `experiments/results/model_pipeline.pkl`.
- Model type: `RandomForestClassifier`.
- Threshold: `0.5`.
- Threshold source: `fixed_default_for_served_rf_model`.
- Calibration: `false`.
- Feature count: 46.
- Artifact SHA256: `3BAA73C949FAB3191EBE6F39F081C504F6E3B82ADAC0AA9EAB388CFEEB50AC36`.

Source: `Phase7Service().model_metadata()` and `experiments/results/metadata.json`.

## Production Model Metrics

Production Random Forest metrics from `experiments/results/rf/metrics.json`:

| Split | ROC-AUC | PR-AUC | Accuracy | Precision | Recall | F1 | Brier | Threshold | Confusion Matrix |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Validation | 0.886143 | 0.876849 | 0.792832 | 0.833333 | 0.711624 | 0.767685 | 0.143925 | 0.50 | TN 1257, FP 191, FN 387, TP 955 |
| Test | 0.899659 | 0.876021 | 0.810519 | 0.820467 | 0.737097 | 0.776551 | 0.135231 | 0.50 | TN 1336, FP 200, FN 326, TP 914 |

## Model Comparison In Frozen Production Results

| Model | Validation ROC-AUC | Validation PR-AUC | Validation F1 | Test ROC-AUC | Test PR-AUC | Test F1 | Test Threshold |
|---|---:|---:|---:|---:|---:|---:|---:|
| Logistic Regression | 0.875494 | 0.867598 | 0.758868 | 0.891123 | 0.857353 | 0.798479 | 0.39 |
| Random Forest | 0.886143 | 0.876849 | 0.767685 | 0.899659 | 0.876021 | 0.776551 | 0.50 |
| XGBoost | 0.893733 | 0.885762 | 0.770216 | 0.899980 | 0.869362 | 0.757655 | 0.50 |

## Twin-Integrity Experiment Results

The twin-integrity experiment under `experiments/twin_integrity_fix` produced a candidate model only. Its metadata says:

- `selected_model_name`: `xgboost`.
- Selection criterion: `highest_validation_roc_auc_then_pr_auc_then_f1`.
- `candidate_only`: `true`.
- `promoted_to_production`: `false`.

Twin-integrity model metrics:

| Model | Validation ROC-AUC | Validation PR-AUC | Validation F1 | Test ROC-AUC | Test PR-AUC | Test F1 | Threshold |
|---|---:|---:|---:|---:|---:|---:|---:|
| Logistic Regression | 0.875830 | 0.868683 | 0.793079 | 0.890260 | 0.857438 | 0.797445 | 0.38 |
| Random Forest | 0.886461 | 0.876173 | 0.806562 | 0.900435 | 0.876282 | 0.807761 | 0.35 |
| XGBoost | 0.892721 | 0.884952 | 0.810401 | 0.900319 | 0.870292 | 0.815361 | 0.36 |

## Why Random Forest Was Retained As Production

The current production service loads `experiments/results/model_pipeline.pkl`, and `Phase7Service().model_metadata()` reports `model_name="rf"`, `model_type="RandomForestClassifier"`, threshold `0.5`, and `production_model_available=true`. The twin-integrity XGBoost is documented as a candidate artifact and was not promoted. Therefore the report should identify XGBoost as an experimental candidate and Random Forest as the actual served production model.

## Feature Importance

Feature importance data exists in model metrics JSON files. Use those files directly for plots or appendix tables. This evidence package does not fabricate a shortened ranking beyond what the metrics artifacts contain.
