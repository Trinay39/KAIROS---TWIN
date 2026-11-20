# KAIROS-TWIN Final Production ML Decision

Decision date: 2026-09-12

## Final Decision

Random Forest remains the final production model for KAIROS-TWIN.

The existing production artifact remains:

`experiments/results/model_pipeline.pkl`

XGBoost was evaluated as a benchmark/candidate during the Twin-integrity ML experiment and was not promoted.

## Why Random Forest Was Retained

The regenerated-feature benchmark showed Random Forest and XGBoost are effectively tied on ranking/calibration quality, with only marginal single-metric differences:

| Model | Test ROC-AUC | Test F1 | Test Brier | Threshold Used In Experiment |
| --- | ---: | ---: | ---: | ---: |
| Random Forest | 0.9004 | 0.8078 | 0.1343 | 0.35 |
| XGBoost | 0.9003 | 0.8154 | 0.1342 | 0.36 |

Those XGBoost advantages are too small to justify changing the established production serving architecture at this stage. Random Forest is already integrated, tested, and proven through the production serving pipeline. Production reliability and defensibility are more important than a marginal benchmark improvement.

Note: the retained production artifact uses its existing production RF threshold, not the regenerated-feature experiment threshold.

## Final Production Configuration

- Production model: Random Forest (`rf`)
- Production artifact: `experiments/results/model_pipeline.pkl`
- Final production threshold: `0.5`
- Threshold source: `fixed_default_for_served_rf_model`
- Calibration status: not calibrated
- Calibration method: none
- Preprocessing pipeline: `SimpleImputer(strategy=mean)` -> `StandardScaler` -> `RandomForestClassifier`
- Feature contract: authoritative 46-feature contract from `ml/feature_contract.py`
- Feature order: verified against the production artifact and `FeatureEngine.FEATURE_NAMES`

## Experiment Evidence Preserved

The Twin-integrity experiment artifacts remain research/benchmark evidence only:

- `experiments/twin_integrity_fix/`
- `experiments/twin_integrity_fix/results/candidate_model_pipeline.pkl`
- `experiments/twin_integrity_fix/REPORT.md`
- `experiments/twin_integrity_fix/final_report.json`

The XGBoost candidate artifact is retained as candidate-only evidence and was not copied into `experiments/results/`.

## Verification

- Hard temporal leakage checks: passed
- Production artifact integrity: verified against archived pre-integrity copy
- Production artifact SHA-256: `3BAA73C949FAB3191EBE6F39F081C504F6E3B82ADAC0AA9EAB388CFEEB50AC36`
- Archived baseline: `experiments/archive/pre_twin_integrity_fix_20260912_112047`
- Archived production artifact was not overwritten or deleted
- Production serving smoke test: `10 passed`
- Full backend test suite: `150 passed, 1 warning`

The ML/backend foundation is frozen for final project completion.
