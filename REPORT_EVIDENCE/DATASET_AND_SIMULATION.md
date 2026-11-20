# Dataset And Simulation

## Raw Synthetic Dataset

Source: `student_simulator.py`.

- Students: 200.
- Days per student: 90.
- Raw daily rows: 18,000.
- Seed: 42.
- Missing rate: 0.15 on observed measurements.
- Baseline sleep: 7.5 hours.
- Sleep sensitivity: 0.50.
- Deadline motivation: 0.35.
- Observation noise: 0.10.

## Raw Columns

`student_id`, `day`, `day_of_week`, `study_hours`, `sleep_hours`, `stress_level`, `recovery_index`, `engagement_score`, `workload_pressure`, `platform_interactions`, `attendance_rate`, `grade`, `assignment_due_today`, `exam_due_today`, `pending_assignments`, `upcoming_deadlines_7d`, `missed_deadline_observed`.

## Simulation Methodology

Each student receives latent stable traits:

- `ability`
- `conscientiousness`
- `resilience`

These traits drive baseline study behavior, stress, recovery, engagement, and prior grade. The simulator then generates daily academic events and behavioral dynamics. Assignment due dates are sampled with probability `0.13` per day; exam due dates are sampled from day 10 onward with probability `0.035` per day.

Daily dynamics include:

- workload from upcoming assignments, upcoming exams, and due-today events;
- study hours influenced by baseline study, deadline motivation, stress, and workload;
- stress influenced by workload, low study, and resilience;
- sleep influenced by stress and high study effort;
- recovery influenced by sleep adequacy and stress;
- engagement influenced by conscientiousness, stress, and recovery;
- grade as a slow-moving noisy academic outcome;
- platform interactions and attendance as observable proxies;
- missed deadline when a due assignment coincides with high stress/workload after resilience adjustment.

## Missing-Data Behavior

Missingness is applied only to observed measurements:

`study_hours`, `sleep_hours`, `stress_level`, `recovery_index`, `engagement_score`, `workload_pressure`, `platform_interactions`, `attendance_rate`, `grade`.

Identifiers, event flags, and label-support columns are not randomly blanked by the simulator.

## Temporal Structure

Source: `core/temporal_sampler.py`.

- Warm-up: days 1-14, no predictions.
- Train: days 15-55.
- Validation: days 56-69.
- Test: days 70-83.
- Outcome-only: days 84-90, used for future labels but not predictions.

Each sample has:

- `X`: features from `StudentTwinState(t)`.
- `y`: overload label from future outcome window `[t+1, t+7]`.
- `t`: current semester day.

The secondary student-level split uses 80/10/10 students with seed 42.

## Modeling Table

The twin-integrity Phase 3 table contains 13,733 valid prediction samples:

- Train: 8,167 rows, days 15-55, positive rate 0.4806.
- Validation: 2,790 rows, days 56-69, positive rate 0.4810.
- Test: 2,776 rows, days 70-83, positive rate 0.4467.

Source: `experiments/twin_integrity_fix/data_phase3/*.csv`.

## Overload Label Definition

Source: `core/label_engine.py`.

The label uses future outcomes in `[t+1, t+7]`. Features never use that future window. Binary overload is true when at least 2 of 5 criteria are triggered. Continuous `strain_index` is an equal-weight severity score clipped to `[0, 1]`.

### Criterion 1: Missed Deadlines

Triggered when the future outcome window has `missed_deadline_observed.sum() >= 1`.

### Criterion 2: Grade Deterioration

Triggered when the worst future grade drops by at least 15 percentage points from the personal baseline. If no baseline is provided, the code uses cohort default `66.3`.

### Criterion 3: Study Collapse

Triggered when mean future study hours are less than 50% of the 30-day baseline. Requires at least 3 future study observations. If no baseline is provided, the code uses default `3.7`.

### Criterion 4: Recovery Failure

Triggered when mean future sleep is below 5.5 hours and cumulative sleep deficit from baseline 7.5 hours is greater than 10 hours. Requires at least 3 future sleep observations.

### Criterion 5: High Stress

Triggered when mean future stress on the mapped 1-5 Likert scale is at least 4.0. The simulator stores internal stress in `[0, 1]`; the label maps it as `1 + 4 * stress_raw`.

## Final Label Rule

`overload_binary = criteria_triggered >= 2`.

`strain_index` uses equal weights of `0.2` for severity components from the five criteria.
