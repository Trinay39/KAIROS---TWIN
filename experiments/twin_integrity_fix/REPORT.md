# KAIROS-TWIN Twin Integrity ML Experiment

- Final production decision: `Random Forest` remains production.
- Production artifact retained: `experiments/results/model_pipeline.pkl`.
- XGBoost status: benchmark/candidate only; not promoted.
- Production RF threshold: `0.5`.
- Production calibration status: not calibrated.
- Production artifact SHA-256: `3BAA73C949FAB3191EBE6F39F081C504F6E3B82ADAC0AA9EAB388CFEEB50AC36`.

- Experiment version: `twin_integrity_fix_v1`
- Baseline archive: `experiments\archive\pre_twin_integrity_fix_20260912_112047`
- Production artifacts modified: `False`
- Hard leakage checks passed: `True`
- Candidate model: `xgboost`
- Candidate suitable: `True`
- Candidate artifact: `experiments\twin_integrity_fix\results\candidate_model_pipeline.pkl`

## New Test Metrics

| Model | ROC-AUC | PR-AUC | Accuracy | Precision | Recall | F1 | Brier | Threshold |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| logistic | 0.8903 | 0.8574 | 0.8058 | 0.7467 | 0.8556 | 0.7974 | 0.1353 | 0.38 |
| rf | 0.9004 | 0.8763 | 0.8073 | 0.7285 | 0.9065 | 0.8078 | 0.1343 | 0.35 |
| xgboost | 0.9003 | 0.8703 | 0.8285 | 0.7855 | 0.8476 | 0.8154 | 0.1342 | 0.36 |

## Feature Quality

- Previous constant features resolved: `['X_attendance_trend_7d', 'X_grades_below_personal_mean_pct', 'X_recovery_score_7d', 'X_submission_rate_14d', 'X_submissions_on_time_pct_14d', 'X_interaction_trend_7d', 'X_interaction_engagement_score']`
- Previous features still constant: `['X_active_subjects_count', 'X_break_rate_7d', 'X_distraction_rate_7d', 'X_focus_quality_7d_avg', 'X_procrastination_index_7d', 'X_pending_assignment_effort_hours', 'X_effort_study_gap_7d', 'X_avg_confidence_7d', 'X_is_exam_period', 'X_recovery_confidence_coupling']`
- Newly constant features: `['X_avg_session_duration_7d']`
- Full quality tables: `reports/old_feature_quality.csv`, `reports/new_feature_quality.csv`
