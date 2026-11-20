# KAIROS-TWIN Report Evidence Package

This folder contains documentation-only evidence for the frozen KAIROS-TWIN implementation. It was generated from the current project files without changing application code, production artifacts, model files, feature contracts, or training logic.

## Files

- `PROJECT_OVERVIEW.md`: report-ready project summary, objective, novelty, users, use cases, and workflow.
- `SYSTEM_ARCHITECTURE.md`: actual architecture, module map, and Mermaid diagram.
- `DATASET_AND_SIMULATION.md`: simulator methodology, raw dataset facts, temporal sampling, and overload label.
- `FEATURE_ENGINEERING.md`: authoritative 46-feature production contract and key formulas.
- `ML_EXPERIMENTS_AND_RESULTS.md`: model comparison, split design, production model, candidate twin-integrity results, and metrics.
- `LEAKAGE_AND_SCIENTIFIC_VALIDATION.md`: leakage safeguards, reproducibility, provenance, artifact integrity, and interpretation boundaries.
- `DIGITAL_TWIN.md`: how `StudentTwinState` is computed and presented.
- `WHAT_IF_AND_SCENARIOS.md`: baseline/counterfactual risk, scenario generator, natural-language parser, and limitations.
- `RECOMMENDATIONS_AND_INTERVENTIONS.md`: recommendation workflow, ranking, logging, responses, follow-up, and Faculty View connection.
- `API_DOCUMENTATION.md`: actual FastAPI endpoints, request/response structures, and authentication.
- `FRONTEND_MODULES.md`: actual React pages, context, client modules, and reusable components.
- `TESTING_AND_VERIFICATION.md`: latest verification results and warnings.
- `LIMITATIONS_AND_FUTURE_WORK.md`: genuine limitations and realistic next steps.
- `RESULTS_TABLES.md`: compact report-ready tables.
- `REPORT_SCREENSHOT_GUIDE.md`: screenshots to capture from the running app and what each demonstrates.
- `FINAL_PROJECT_FACTS.json`: machine-readable verified project facts.

## Most Important For Report Writing

Start with `PROJECT_OVERVIEW.md`, `SYSTEM_ARCHITECTURE.md`, `DATASET_AND_SIMULATION.md`, `FEATURE_ENGINEERING.md`, `ML_EXPERIMENTS_AND_RESULTS.md`, and `RESULTS_TABLES.md`. Use `LEAKAGE_AND_SCIENTIFIC_VALIDATION.md` to support methodology claims and `TESTING_AND_VERIFICATION.md` for implementation evidence.

## Traceability

Important source files include `student_simulator.py`, `core/label_engine.py`, `core/temporal_sampler.py`, `core/twin_engine.py`, `core/feature_engine.py`, `simulation/prediction_service.py`, `simulation/scenario_generator.py`, `simulation/counterfactual_engine.py`, `simulation/scenario_ranker.py`, `intervention/recommendation.py`, `phase6_orchestrator.py`, `api/main.py`, `api/schemas.py`, `api/service.py`, and `frontend/src`.

## Unresolved Gaps And Contradictions

- Production serving uses `experiments/results/model_pipeline.pkl` with Random Forest, threshold `0.5`, and `calibrated=false`. The later twin-integrity experiment selected an XGBoost candidate by validation ROC-AUC/PR-AUC/F1, but its metadata says `candidate_only=true` and `promoted_to_production=false`; this is documented as a candidate, not production.
- The raw simulator design is 200 students x 90 days = 18,000 rows. The Phase 3 modeling table has 13,733 valid samples after warm-up, prediction-day limits, future label availability, and missing/unknown-label filtering.
- Some production features are unavailable in the simulator and are represented by defaults or adapter-compatible constants to preserve the frozen 46-feature contract. These are documented rather than hidden.
- `core/label_engine.py` defines `STRESS_RAW_THRESHOLD=0.65`, but the implemented high-stress criterion maps raw stress to Likert and checks mean Likert stress >= 4.0. The implemented criterion is the source of truth.
- Frontend tests pass but emit Recharts zero-size chart warnings in jsdom. The production build passes but emits a Vite warning that the main JS chunk is larger than 500 kB.
