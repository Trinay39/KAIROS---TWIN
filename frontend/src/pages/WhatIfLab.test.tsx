import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { SimulationResponse, StudentTwinState } from '../types';
import WhatIfLab from './WhatIfLab';

const endpointMocks = vi.hoisted(() => ({
  simulate: vi.fn(),
}));

vi.mock('../api/endpoints', () => ({
  endpoints: endpointMocks,
}));

function twin(): StudentTwinState {
  return {
    student_id: 'STU_BALANCED',
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

vi.mock('../context/DemoContext', () => ({
  useDemo: () => ({
    state: {
      input: { student_id: 'STU_BALANCED', day: 35, study_hours: 4, sleep_hours: 6.5, stress_level: 5, grade: 80, attendance_rate: 0.9, missed_deadline_observed: 0 },
      twin: twin(),
    },
  }),
}));

function simulation(): SimulationResponse {
  return {
    student_id: 'STU_BALANCED',
    day: 35,
    results: [{
      scenario_id: 'nl_sleep_more_35',
      scenario_type: 'increase_sleep',
      scenario_description: 'Natural-language sleep increase',
      baseline_probability: 0.5,
      counterfactual_probability: 0.4,
      risk_delta: -0.1,
      risk_reduction_percentage: 20,
      baseline_strain: null,
      counterfactual_strain: null,
      strain_delta: null,
      changed_features_count: 2,
      unchanged_features_count: 44,
      interpretation: 'Modest reduction',
    }],
    ranked_scenarios: [],
  };
}

beforeEach(() => {
  endpointMocks.simulate.mockResolvedValue(simulation());
});

describe('WhatIfLab', () => {
  it('renders interpreted natural-language changes and simulation result', async () => {
    render(<WhatIfLab />);

    fireEvent.change(screen.getByPlaceholderText('I need to sleep more and study less'), {
      target: { value: 'I need to sleep more and study less' },
    });
    fireEvent.click(screen.getByText('Interpret & Run'));

    expect(await screen.findByText('Sleep +1.0 hour/night')).toBeInTheDocument();
    expect(screen.getByText('Study -1.0 hour/day')).toBeInTheDocument();
    expect((await screen.findAllByText('Natural-language sleep increase')).length).toBeGreaterThan(0);
    expect(screen.getByText('Estimated relative change: 10.0 percentage points lower.')).toBeInTheDocument();
  });

  it('renders no material change when probabilities are effectively unchanged', async () => {
    endpointMocks.simulate.mockResolvedValue({
      ...simulation(),
      results: [{
        ...simulation().results[0],
        counterfactual_probability: 0.5004,
        risk_delta: 0.0004,
      }],
    });

    render(<WhatIfLab />);

    fireEvent.click(screen.getByText('Sleep more'));
    fireEvent.click(screen.getByText('Run Selected Scenario'));
    expect((await screen.findAllByText('No material change under the current model.')).length).toBeGreaterThan(0);
  });
});
