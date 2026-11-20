# Feature Engineering

## Production Contract

Source: `core/feature_engine.py`.

The production feature contract contains exactly 46 features in the following authoritative order:

1. `attendance_rate_7d`
2. `attendance_trend_7d`
3. `recent_grades_mean`
4. `grade_trend_30d`
5. `grades_below_personal_mean_pct`
6. `active_subjects_count`
7. `missed_deadlines_14d`
8. `avg_study_hours_3d`
9. `avg_study_hours_7d`
10. `study_variability_7d`
11. `study_consistency_score`
12. `avg_session_duration_7d`
13. `break_rate_7d`
14. `distraction_rate_7d`
15. `focus_quality_7d_avg`
16. `procrastination_index_7d`
17. `avg_sleep_hours_7d`
18. `sleep_variability_7d`
19. `sleep_deficit_7d_hours`
20. `sleep_debt_severity`
21. `rest_days_7d`
22. `recovery_ratio_7d`
23. `recovery_score_7d`
24. `recovery_deficit_score`
25. `pending_assignment_count`
26. `pending_assignment_effort_hours`
27. `deadline_density_trend_7d`
28. `workload_pressure_score_7d`
29. `submission_rate_14d`
30. `submissions_on_time_pct_14d`
31. `effort_study_gap_7d`
32. `platform_interactions_7d_avg`
33. `interaction_trend_7d`
34. `interaction_engagement_score`
35. `avg_stress_7d`
36. `avg_confidence_7d`
37. `week_of_semester`
38. `day_of_week_sine`
39. `day_of_week_cosine`
40. `is_midterm_period`
41. `is_exam_period`
42. `days_until_exam_period`
43. `workload_recovery_imbalance`
44. `deadline_urgency_effort_ratio`
45. `study_stress_coherence`
46. `recovery_confidence_coupling`

## Feature Categories

- Academic: features 1-7.
- Behavioral: features 8-16.
- Recovery: features 17-24.
- Workload: features 25-31.
- Engagement: features 32-36.
- Temporal: features 37-42.
- Interaction: features 43-46.

## Observed, Derived, And Imputed Values

The twin state is computed from observed daily rows and rolling historical windows in `core/twin_engine.py`. `FieldProvenance` marks fields as observed, derived, predicted, or imputed defaults. Some production features are unavailable from the simulator or live observation schema and are defaulted to preserve the frozen artifact contract, including break rate, distraction rate, focus quality, procrastination index, confidence, effort hours, and effort-study gap.

## Important Formulas

- Attendance rate: mean `attendance_rate` over the last 7 valid observations.
- Attendance trend: OLS slope over last 7 valid attendance observations.
- Recent grade mean: mean of last 5 observed grades, normalized by dividing by 100.
- Grade trend: OLS slope over last 5 observed grades, normalized by 100.
- Grades below personal mean percentage: share of recent 5 grades below prior grade baseline.
- Missed deadlines: sum of `missed_deadline_observed` over last 14 observations.
- Study averages: means over 3-day, 7-day, and 14-day windows.
- Study variability: standard deviation over mean for 7-day study hours.
- Study consistency: `1 - min(1, study_variability_7d / 2)`.
- Average session duration: 7-day study hours divided by 7-day study sessions when session data exists.
- Sleep deficit: sum of positive `(7.5 - sleep_hours)` over last 7 observations.
- Sleep debt severity: `sleep_deficit_7d_hours / 14`, capped at 1.
- Rest days: count of last-7 days with `study_hours < 0.5`.
- Recovery ratio: 7-day sleep sum divided by `(7-day study sum + 0.1)`.
- Recovery score: mean `recovery_index` over last 7 observations, or a fallback based on sleep adequacy and debt.
- Academic load score: equal-weight mean of workload pressure, pending assignments divided by 10, and known next-7 deadline density divided by 7.
- Deadline density trend: OLS slope over last 7 `upcoming_deadlines_7d`.
- Workload pressure: mean `workload_pressure` over last 7 observations.
- Submission metrics: `(due_count - missed_count) / due_count` over the last 14 days when due assignments exist.
- Platform interactions: mean and OLS trend over last 7 observations.
- Engagement composite: mean `engagement_score` over last 7 observations.
- Stress metric: internal simulator stress mapped to Likert as `1 + 4 * mean(stress_level)`.
- Week of semester: `(day - 1) // 7 + 1`.
- Day of week cyclic encoding: sine and cosine of `2*pi*day_of_week/7`.
- Exam period: day >= 85.
- Midterm period: day 29 through 49.
- Days until exam period: `max(0, 85 - day)`.
- Workload-recovery imbalance: `(workload * 100) / (recovery_ratio + 0.1) - 50`.
- Deadline urgency effort ratio: `deadline_density_trend_7d / (avg_study_hours_7d + 0.1)`, or 0 when trend is 0.
- Study-stress coherence: `-0.5 * (avg_stress_7d - 3.0) / 2.0`.
- Recovery-confidence coupling: `(recovery_score_7d - 0.5) * (avg_confidence_7d - 3.0) / 5.0`.

## Leakage Protections

`TwinEngine.compute_state` filters observations to `day <= t`. `FeatureEngine` operates only on `StudentTwinState(t)`. Labels use future `[t+1, t+7]`, but those future rows are not passed into feature extraction. API validation rejects future labels and outcome fields such as `y_binary`, `y_continuous`, `split`, `outcome_window`, and keys starting with `c_` or `y_`.
