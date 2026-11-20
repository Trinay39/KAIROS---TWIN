# Results Tables

## Dataset Statistics

| Item | Value | Source |
|---|---:|---|
| Students | 200 | `student_simulator.py` |
| Days per student | 90 | `student_simulator.py` |
| Raw rows | 18,000 | 200 x 90 |
| Simulator seed | 42 | `SimulatorConfig` |
| Missing rate | 0.15 | `SimulatorConfig` |
| Modeling rows | 13,733 | `experiments/twin_integrity_fix/data_phase3/combined.csv` |
| Train rows | 8,167 | `train.csv` |
| Validation rows | 2,790 | `val.csv` |
| Test rows | 2,776 | `test.csv` |

## Feature Groups

| Group | Count | Feature Index Range |
|---|---:|---|
| Academic | 7 | 1-7 |
| Behavioral | 9 | 8-16 |
| Recovery | 8 | 17-24 |
| Workload | 7 | 25-31 |
| Engagement | 5 | 32-36 |
| Temporal | 6 | 37-42 |
| Interaction | 4 | 43-46 |
| Total | 46 | 1-46 |

## Production Model Metadata

| Field | Value |
|---|---|
| Production model | Random Forest |
| Model type | `RandomForestClassifier` |
| Artifact | `experiments/results/model_pipeline.pkl` |
| Threshold | 0.5 |
| Calibration | false |
| Feature count | 46 |
| Hash | `3BAA73C949FAB3191EBE6F39F081C504F6E3B82ADAC0AA9EAB388CFEEB50AC36` |

## Frozen Production Model Comparison

| Model | Validation ROC-AUC | Validation PR-AUC | Validation F1 | Test ROC-AUC | Test PR-AUC | Test F1 |
|---|---:|---:|---:|---:|---:|---:|
| Logistic Regression | 0.875494 | 0.867598 | 0.758868 | 0.891123 | 0.857353 | 0.798479 |
| Random Forest | 0.886143 | 0.876849 | 0.767685 | 0.899659 | 0.876021 | 0.776551 |
| XGBoost | 0.893733 | 0.885762 | 0.770216 | 0.899980 | 0.869362 | 0.757655 |

## Production Random Forest Metrics

| Split | ROC-AUC | PR-AUC | Accuracy | Precision | Recall | F1 | Brier | Threshold |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Validation | 0.886143 | 0.876849 | 0.792832 | 0.833333 | 0.711624 | 0.767685 | 0.143925 | 0.50 |
| Test | 0.899659 | 0.876021 | 0.810519 | 0.820467 | 0.737097 | 0.776551 | 0.135231 | 0.50 |

## Twin-Integrity Candidate Metrics

| Model | Validation ROC-AUC | Validation PR-AUC | Validation F1 | Test ROC-AUC | Test PR-AUC | Test F1 | Promoted |
|---|---:|---:|---:|---:|---:|---:|---|
| Logistic Regression | 0.875830 | 0.868683 | 0.793079 | 0.890260 | 0.857438 | 0.797445 | No |
| Random Forest | 0.886461 | 0.876173 | 0.806562 | 0.900435 | 0.876282 | 0.807761 | No |
| XGBoost | 0.892721 | 0.884952 | 0.810401 | 0.900319 | 0.870292 | 0.815361 | No, candidate only |

## Test Suite Results

| Area | Result |
|---|---|
| Full backend | 154 passed, 1 warning |
| Production serving | 10 passed |
| Phase 7 API | 24 passed, 1 warning |
| Phase 8 adapter | 4 passed, 1 warning |
| Frontend tests | 30 passed |
| Typecheck | passed |
| Lint | passed |
| Build | passed |

## System Components

| Component | Implementation |
|---|---|
| Frontend | React/TypeScript/Vite under `frontend/src` |
| API | FastAPI in `api/main.py` |
| Service facade | `api/service.py` |
| Digital twin | `core/twin_engine.py` |
| Feature contract | `core/feature_engine.py` |
| Production ML serving | `simulation/prediction_service.py` |
| Scenarios | `simulation/scenario_*` |
| Recommendations | `phase6_orchestrator.py`, `intervention/recommendation.py` |
| Intervention logging | `intervention/intervention_registry.py` |
| Outcome tracking | `intervention/outcome_tracker.py` |
