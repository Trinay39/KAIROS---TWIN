# Digital Twin

## Purpose

The Student Digital Twin is an intermediate representation of a student's current academic, behavioral, recovery, workload, engagement, temporal, prediction, and history state. It is different from a normal prediction model because it stores structured state and provenance before prediction, diagnostics, scenarios, and recommendations are run.

Source files: `core/schemas.py`, `core/twin_engine.py`, `api/service.py`.

## Computation Flow

Input observations -> historical state -> rolling features -> current `StudentTwinState` -> academic state -> recovery state -> engagement state -> stress state -> prediction.

In implementation:

1. `/states/compute` receives `student_id`, `day`, observations, and `data_source`.
2. `Phase7Service` validates that observations are not future rows and contain required canonical fields.
3. For synthetic demo students, deterministic demo history can be merged through the selected day.
4. `TwinEngine.compute_state` filters rows to `day <= t`.
5. The engine builds:
   - `raw_latest`
   - `academic`
   - `behavioral`
   - `recovery`
   - `workload`
   - `engagement`
   - `temporal`
   - `history`
   - `provenance`
6. Prediction uses the 46-feature production contract and frozen model.

## Twin State Sections

- Academic: attendance, grades, grade trend, deadlines, academic load.
- Behavioral: study hours, study variability, consistency, session duration if available.
- Recovery: sleep, sleep deficit, sleep debt, rest days, recovery ratio, recovery score.
- Workload: pending assignments, deadline trend, pressure, submission rates.
- Engagement: platform interactions, engagement score, stress mapped to 1-5 Likert.
- Temporal: week, day of week, midterm/exam period, days until exam period.
- History: observation count and completeness count.
- Provenance: field source and formula metadata.

## What The Student Sees

The frontend exposes the twin through the Digital Twin page, Risk Intelligence, What-If Lab, Recommendations, and Student History. The student can inspect current risk, state metrics, diagnostics, counterfactual scenario estimates, recommendations, and history charts.

## What Faculty View Sees

Faculty View combines current estimated risk, academic load, recovery, engagement, stress, attendance, study behavior, intervention counts, historical observations, intervention records, and system analytics. Source: `frontend/src/pages/FacultyView.tsx`, `/analytics/system`, `/students/{student_id}/history`.

## Scientific Role

The twin gives the project a traceable state layer. Predictions are not produced directly from raw UI fields; they are produced from a validated, temporally filtered `StudentTwinState(t)` and a fixed feature contract.
