import { describe, expect, it } from 'vitest';
import type { StudentTwinState } from '../types';
import { parseNaturalLanguageScenario } from './scenarioIntent';

function twin(): StudentTwinState {
  return {
    student_id: 'STU_TEST',
    date: null,
    day: 35,
    state_version: 1,
    computed_at: '2026-09-15T00:00:00',
    data_source: 'synthetic',
    raw_latest: {},
    academic: { attendance_rate_7d: null, attendance_trend_7d: null, attendance_rate_30d: null, recent_grades_mean: null, grade_trend_30d: null, grades_below_personal_mean_pct: null, active_subjects_count: 0, academic_load_score: null, missed_deadlines_14d: 0 },
    behavioral: { avg_study_hours_3d: null, avg_study_hours_7d: 4, avg_study_hours_14d: null, study_hours_trend_7d: null, study_variability_7d: null, study_consistency_score: null, avg_session_duration_7d: null, break_rate_7d: null, distraction_rate_7d: null, focus_quality_7d_avg: null, procrastination_index_7d: null },
    recovery: { recovery_baseline_hours: 7.5, avg_sleep_hours_7d: 6.5, avg_sleep_hours_14d: null, sleep_variability_7d: null, sleep_deficit_7d_hours: null, sleep_debt_severity: null, rest_days_7d: 0, recovery_ratio_7d: null, recovery_score_7d: null },
    workload: { deadline_schedule_published: true, pending_assignment_count: 0, pending_assignment_effort_hours: null, deadline_density_next_7_known: null, deadline_density_trend_7d: null, workload_pressure_score_7d: null, submission_rate_14d: null, submissions_on_time_pct_14d: null, effort_study_gap_7d: null },
    engagement: { platform_interactions_7d_avg: null, interaction_trend_7d: null, interaction_engagement_score: null, avg_stress_7d: null, stress_trend_7d: null, avg_confidence_7d: null, avg_wellbeing_7d: null, engagement_composite_score: null },
    temporal: { day_of_semester: 35, week_of_semester: 5, day_of_week: 0, is_exam_period: false, is_midterm_period: false, semester_phase: 'mid', days_until_exam_period: 50 },
    predictions: { model_name: '', model_version: '', prediction_timestamp: null, overload_risk_probability: null, overload_label_binary: null, threshold_applied: 0.5, strain_index: null, feature_importances: {}, model_confidence: 0.5 },
    history: { total_observations: 7, observations_with_full_data: 7, avg_overload_risk_30d: null, overload_risk_trend_30d: null, peak_overload_risk_30d: null, interventions_received_lifetime: 0, interventions_accepted_lifetime: 0, intervention_acceptance_rate: null, state_updates_count: 1, days_with_high_stress_30d: 0, days_with_sleep_deficit_30d: 0, cohort_percentile_risk: null },
  };
}

describe('natural-language scenario parser', () => {
  it('parses combined sleep-more and study-less intent with defaults', () => {
    const parsed = parseNaturalLanguageScenario('I need to sleep more and study less', twin(), 35);

    expect(parsed?.changes).toEqual(['Sleep +1.0 hour/night', 'Study -1.0 hour/day']);
    expect(parsed?.scenarios).toEqual([
      expect.objectContaining({ scenario_type: 'INCREASE_SLEEP', parameters: { hours_per_night: 7.5 } }),
      expect.objectContaining({ scenario_type: 'INCREASE_STUDY_TIME', parameters: { hours_per_day: -1, days: 7 } }),
    ]);
  });

  it('parses explicit sleep and study quantities', () => {
    const parsed = parseNaturalLanguageScenario('I want to sleep 1 hour more and study 30 minutes less', twin(), 35);

    expect(parsed?.changes).toEqual(['Sleep +1.0 hour/night', 'Study -0.5 hour/day']);
    expect(parsed?.scenarios[1]).toEqual(expect.objectContaining({
      scenario_type: 'INCREASE_STUDY_TIME',
      parameters: { hours_per_day: -0.5, days: 7 },
    }));
  });

  it('parses explicit sleep target', () => {
    const parsed = parseNaturalLanguageScenario('I want to increase my sleep to 8 hours', twin(), 35);

    expect(parsed?.changes).toEqual(['Sleep target 8.0 hours/night']);
    expect(parsed?.scenarios[0]).toEqual(expect.objectContaining({
      scenario_type: 'INCREASE_SLEEP',
      parameters: { hours_per_night: 8 },
    }));
  });

  it('rejects ambiguous text', () => {
    expect(parseNaturalLanguageScenario('I feel unsure about everything', twin(), 35)).toBeNull();
    expect(parseNaturalLanguageScenario('I want to change my routine', twin(), 35)).toBeNull();
  });

  it('maps deadline pressure separately from workload', () => {
    const parsed = parseNaturalLanguageScenario('I want to reduce deadline pressure', twin(), 35);

    expect(parsed?.changes).toEqual(['Spread deadlines to reduce density peaks']);
    expect(parsed?.scenarios[0]).toEqual(expect.objectContaining({
      scenario_type: 'REDUCE_DEADLINE_DENSITY',
      parameters: {},
    }));
  });
});
