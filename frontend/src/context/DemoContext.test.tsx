import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import TopBar from '../components/TopBar';
import type {
  DiagnosticsResponse,
  FollowupOutcomeResponse,
  HealthStatus,
  InterventionLog,
  PredictionResponse,
  Recommendation,
  SimulationResponse,
  StudentTwinState,
} from '../types';
import { DemoProvider, useDemo } from './DemoContext';

const endpointMocks = vi.hoisted(() => ({
  health: vi.fn(),
  modelMetadata: vi.fn(),
  computeState: vi.fn(),
  predict: vi.fn(),
  diagnostics: vi.fn(),
  scenarios: vi.fn(),
  simulate: vi.fn(),
  recommend: vi.fn(),
  logIntervention: vi.fn(),
  updateResponse: vi.fn(),
  followup: vi.fn(),
  history: vi.fn(),
  analytics: vi.fn(),
}));

vi.mock('../api/endpoints', () => ({
  endpoints: endpointMocks,
}));

function twinFor(studentId: string, day: number): StudentTwinState {
  return {
    student_id: studentId,
    date: null,
    day,
    state_version: 1,
    computed_at: '2026-09-11T00:00:00',
    data_source: 'synthetic',
    raw_latest: {},
    academic: {
      attendance_rate_7d: 0.9,
      attendance_trend_7d: null,
      attendance_rate_30d: null,
      recent_grades_mean: null,
      grade_trend_30d: null,
      grades_below_personal_mean_pct: null,
      active_subjects_count: 0,
      academic_load_score: 0.4,
      missed_deadlines_14d: 0,
    },
    behavioral: {
      avg_study_hours_3d: null,
      avg_study_hours_7d: 4.5,
      avg_study_hours_14d: null,
      study_hours_trend_7d: null,
      study_variability_7d: null,
      study_consistency_score: 0.8,
      avg_session_duration_7d: null,
      break_rate_7d: null,
      distraction_rate_7d: null,
      focus_quality_7d_avg: null,
      procrastination_index_7d: null,
    },
    recovery: {
      recovery_baseline_hours: 7.5,
      avg_sleep_hours_7d: 8,
      avg_sleep_hours_14d: null,
      sleep_variability_7d: null,
      sleep_deficit_7d_hours: null,
      sleep_debt_severity: null,
      rest_days_7d: 0,
      recovery_ratio_7d: null,
      recovery_score_7d: 0.9,
    },
    workload: {
      deadline_schedule_published: true,
      pending_assignment_count: 0,
      pending_assignment_effort_hours: null,
      deadline_density_next_7_known: null,
      deadline_density_trend_7d: null,
      workload_pressure_score_7d: 0.3,
      submission_rate_14d: null,
      submissions_on_time_pct_14d: null,
      effort_study_gap_7d: null,
    },
    engagement: {
      platform_interactions_7d_avg: null,
      interaction_trend_7d: null,
      interaction_engagement_score: null,
      avg_stress_7d: 2,
      stress_trend_7d: null,
      avg_confidence_7d: null,
      avg_wellbeing_7d: null,
      engagement_composite_score: 0.7,
    },
    temporal: {
      day_of_semester: day,
      week_of_semester: 5,
      day_of_week: 1,
      is_exam_period: false,
      is_midterm_period: false,
      semester_phase: 'mid',
      days_until_exam_period: 40,
    },
    predictions: {
      model_name: '',
      model_version: '',
      prediction_timestamp: null,
      overload_risk_probability: null,
      overload_label_binary: null,
      threshold_applied: 0.5,
      strain_index: null,
      feature_importances: {},
      model_confidence: 0.5,
    },
    history: {
      total_observations: 7,
      observations_with_full_data: 7,
      avg_overload_risk_30d: null,
      overload_risk_trend_30d: null,
      peak_overload_risk_30d: null,
      interventions_received_lifetime: 0,
      interventions_accepted_lifetime: 0,
      intervention_acceptance_rate: null,
      state_updates_count: 1,
      days_with_high_stress_30d: 0,
      days_with_sleep_deficit_30d: 0,
      cohort_percentile_risk: null,
    },
  };
}

function prediction(): PredictionResponse {
  return {
    overload_probability: 0.62,
    overload_prediction: true,
    strain_index: null,
    model_name: 'rf',
    model_version: '1.0',
    timestamp: '2026-09-11T00:00:00',
    day: 35,
    top_contributing_features: {},
    confidence_info: {},
  };
}

function recommendation(): Recommendation {
  return {
    scenario_id: 'rec-1',
    scenario_type: 'INCREASE_SLEEP',
    scenario_description: 'Improve sleep to 8 hours/night',
    baseline_risk: 0.7,
    counterfactual_risk: 0.55,
    risk_delta: 0.15,
    risk_reduction_percentage: 21.4,
    strain_delta: null,
    changed_features_count: 0,
    top_changed_features: [],
    explanation: 'Model-estimated recommendation based on synthetic data.',
    primary_diagnoses: [],
    confidence: 'medium',
    caveats: ['Trained on synthetic data only'],
    timestamp: '2026-09-11T00:00:00',
    student_id: 'STU_BALANCED',
    day: 35,
  };
}

function alternateRecommendation(): Recommendation {
  return {
    ...recommendation(),
    scenario_id: 'rec-2',
    scenario_type: 'REDUCE_WORKLOAD',
    scenario_description: 'Reduce workload pressure',
  };
}

function diagnostics(): DiagnosticsResponse {
  return {
    student_id: 'STU_BALANCED',
    day: 35,
    diagnoses: { RecoveryAgent: [] },
    statistics: {
      total_diagnoses: 0,
      by_severity: {},
      by_agent: {},
      top_issues: [],
    },
  };
}

function simulation(): SimulationResponse {
  return {
    student_id: 'STU_BALANCED',
    day: 35,
    results: [],
    ranked_scenarios: [],
  };
}

function interventionLog(response: string): InterventionLog {
  return {
    intervention_id: `int-${response}`,
    persistence_base: 'data/phase7',
    record: {
      intervention_id: `int-${response}`,
      student_id: 'STU_BALANCED',
      timestamp: '2026-09-11T00:00:00',
      scenario_id: 'rec-1',
      scenario_type: 'INCREASE_SLEEP',
      scenario_description: 'Improve sleep',
      baseline_risk: 0.7,
      counterfactual_risk: 0.55,
      predicted_risk_delta: 0.15,
      predicted_strain_delta: null,
      status: response,
      offered_at_day: 35,
      accepted_at_day: response === 'accepted' ? 35 : null,
      completed_at_day: null,
      student_response: response as InterventionLog['record']['student_response'],
      student_feedback: null,
      actual_risk_at_day7: null,
      actual_risk_delta: null,
      outcome_report_id: null,
      agent_diagnoses: [],
      recommendation_confidence: 'medium',
    },
  };
}

function followupOutcome(): FollowupOutcomeResponse {
  return {
    outcome_id: 'outcome-int-accepted',
    record: interventionLog('accepted').record,
    report: {
      outcome_id: 'outcome-int-accepted',
      intervention_id: 'int-accepted',
      student_id: 'STU_BALANCED',
      timestamp: '2026-09-11T00:00:00',
      baseline_day: 35,
      baseline_risk: 0.7,
      baseline_strain: null,
      predicted_risk_delta: 0.15,
      predicted_strain_delta: null,
      predicted_counterfactual_risk: 0.55,
      followup_day: 42,
      actual_risk_at_day7: 0.52,
      actual_risk_delta: -0.18,
      actual_strain_at_day7: null,
      actual_strain_delta: null,
      state_changes: {},
      student_self_report: 'partial',
      student_feedback_text: 'Demo follow-up observation recorded from the current synthetic profile.',
      was_successful: true,
      prediction_accuracy: 0.82,
      confidence: 0.8,
    },
  };
}

function healthyStatus(overrides: Partial<HealthStatus> = {}): HealthStatus {
  return {
    status: 'ok',
    phase: '7',
    prototype: true,
    model_loaded: true,
    production_model_available: true,
    calibrated: false,
    persistence_base: 'data/phase7',
    timestamp: '2026-09-11T00:00:00',
    ...overrides,
  };
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((res) => {
    resolve = res;
  });
  return { promise, resolve };
}

function Probe() {
  const { state, activePreset, applyScenario, computeTwin, predictRisk, runDiagnostics, runWhatIf, generateRec, generateMoreRec, recordDecision, recordFollowup } = useDemo();

  return (
    <div>
      <span data-testid="student">{state.input.student_id}</span>
      <span data-testid="active">{activePreset ?? 'none'}</span>
      <span data-testid="twin">{state.twin?.student_id ?? 'none'}</span>
      <span data-testid="prediction">{state.prediction?.overload_probability ?? 'none'}</span>
      <span data-testid="diagnostics">{state.diagnostics?.student_id ?? 'none'}</span>
      <span data-testid="simulation">{state.sim?.student_id ?? 'none'}</span>
      <span data-testid="recommendation">{state.rec?.scenario_id ?? 'none'}</span>
      <span data-testid="recommendations">{state.recommendations.length}</span>
      <span data-testid="recommendation-message">{state.recommendationMessage ?? 'none'}</span>
      <span data-testid="decision">{state.decision ?? 'none'}</span>
      <span data-testid="decision-status">{state.status.decision}</span>
      <span data-testid="intervention">{state.interventionId ?? 'none'}</span>
      <span data-testid="followup">{state.followup?.outcome_id ?? 'none'}</span>
      <button onClick={() => applyScenario('OVERLOADED')}>overloaded</button>
      <button onClick={() => applyScenario('RECOVERY')}>recovery</button>
      <button onClick={computeTwin}>compute</button>
      <button onClick={predictRisk}>predict</button>
      <button onClick={runDiagnostics}>diagnose</button>
      <button onClick={runWhatIf}>simulate</button>
      <button onClick={generateRec}>recommend</button>
      <button onClick={generateMoreRec}>more</button>
      <button onClick={() => recordDecision('accepted')}>accepted</button>
      <button onClick={() => recordDecision('rejected')}>rejected</button>
      <button onClick={() => recordDecision('deferred')}>deferred</button>
      <button onClick={() => recordDecision('ask_more')}>ask_more</button>
      <button onClick={recordFollowup}>followup</button>
    </div>
  );
}

function renderProbe() {
  return render(
    <DemoProvider>
      <Probe />
    </DemoProvider>,
  );
}

beforeEach(() => {
  vi.useRealTimers();
  endpointMocks.health.mockResolvedValue(healthyStatus());
  endpointMocks.computeState.mockResolvedValue(twinFor('STU_BALANCED', 35));
  endpointMocks.predict.mockResolvedValue(prediction());
  endpointMocks.diagnostics.mockResolvedValue(diagnostics());
  endpointMocks.simulate.mockResolvedValue(simulation());
  endpointMocks.recommend.mockResolvedValue(recommendation());
  endpointMocks.logIntervention.mockImplementation(({ student_response }: { student_response: string }) =>
    Promise.resolve(interventionLog(student_response)),
  );
  endpointMocks.followup.mockResolvedValue(followupOutcome());
});

afterEach(() => {
  Object.values(endpointMocks).forEach((mock) => mock.mockReset());
});

describe('DemoContext reliability', () => {
  it('loads a valid initial demo student state', () => {
    renderProbe();

    expect(screen.getByTestId('student')).toHaveTextContent('STU_BALANCED');
    expect(screen.getByTestId('active')).toHaveTextContent('none');
  });

  it('updates the active scenario and student when a scenario is selected', () => {
    renderProbe();

    fireEvent.click(screen.getByText('overloaded'));

    expect(screen.getByTestId('active')).toHaveTextContent('OVERLOADED');
    expect(screen.getByTestId('student')).toHaveTextContent('STU_OVERLOADED');
  });

  it('clears stale downstream data when the selected scenario changes', async () => {
    renderProbe();

    fireEvent.click(screen.getByText('compute'));
    await screen.findByText('STU_BALANCED', { selector: '[data-testid="twin"]' });
    fireEvent.click(screen.getByText('predict'));
    await screen.findByText('0.62', { selector: '[data-testid="prediction"]' });
    fireEvent.click(screen.getByText('diagnose'));
    await screen.findByText('STU_BALANCED', { selector: '[data-testid="diagnostics"]' });
    fireEvent.click(screen.getByText('simulate'));
    await screen.findByText('STU_BALANCED', { selector: '[data-testid="simulation"]' });
    fireEvent.click(screen.getByText('recommend'));
    await screen.findByText('rec-1', { selector: '[data-testid="recommendation"]' });

    fireEvent.click(screen.getByText('recovery'));

    expect(screen.getByTestId('student')).toHaveTextContent('STU_RECOVERY');
    expect(screen.getByTestId('twin')).toHaveTextContent('none');
    expect(screen.getByTestId('prediction')).toHaveTextContent('none');
    expect(screen.getByTestId('diagnostics')).toHaveTextContent('none');
    expect(screen.getByTestId('simulation')).toHaveTextContent('none');
    expect(screen.getByTestId('recommendation')).toHaveTextContent('none');
    expect(screen.getByTestId('followup')).toHaveTextContent('none');
  });

  it('ignores stale async responses after a newer scenario is selected', async () => {
    const pendingTwin = deferred<StudentTwinState>();
    endpointMocks.computeState.mockReturnValueOnce(pendingTwin.promise);
    renderProbe();

    fireEvent.click(screen.getByText('compute'));
    fireEvent.click(screen.getByText('overloaded'));

    await act(async () => {
      pendingTwin.resolve(twinFor('STU_BALANCED', 35));
      await pendingTwin.promise;
      await Promise.resolve();
    });

    expect(screen.getByTestId('student')).toHaveTextContent('STU_OVERLOADED');
    expect(screen.getByTestId('twin')).toHaveTextContent('none');
  });

  it('submits only canonical intervention decision values', async () => {
    renderProbe();

    fireEvent.click(screen.getByText('compute'));
    await screen.findByText('STU_BALANCED', { selector: '[data-testid="twin"]' });
    fireEvent.click(screen.getByText('recommend'));
    await screen.findByText('rec-1', { selector: '[data-testid="recommendation"]' });

    for (const decision of ['accepted', 'rejected', 'deferred', 'ask_more']) {
      fireEvent.click(screen.getByText(decision));
      await waitFor(() => expect(endpointMocks.logIntervention).toHaveBeenLastCalledWith(expect.objectContaining({
        recommendation: expect.objectContaining({ scenario_id: 'rec-1' }),
        student_response: decision,
      })));
    }

    const sentResponses = endpointMocks.logIntervention.mock.calls.map(([payload]) => payload.student_response);
    expect(sentResponses).toEqual(['accepted', 'rejected', 'deferred', 'ask_more']);
    expect(sentResponses).not.toContain('accept');
    expect(sentResponses).not.toContain('reject');
    expect(sentResponses).not.toContain('defer');
  });

  it('records follow-up outcomes through the existing backend contract', async () => {
    renderProbe();

    fireEvent.click(screen.getByText('compute'));
    await screen.findByText('STU_BALANCED', { selector: '[data-testid="twin"]' });
    fireEvent.click(screen.getByText('recommend'));
    await screen.findByText('rec-1', { selector: '[data-testid="recommendation"]' });
    fireEvent.click(screen.getByText('accepted'));
    await screen.findByText('int-accepted', { selector: '[data-testid="intervention"]' });

    fireEvent.click(screen.getByText('followup'));

    await screen.findByText('outcome-int-accepted', { selector: '[data-testid="followup"]' });
    expect(endpointMocks.followup).toHaveBeenCalledWith('int-accepted', expect.objectContaining({
      followup_day: 42,
      student_feedback: 'partial',
      observations: expect.arrayContaining([
        expect.objectContaining({ day: 42 }),
      ]),
    }));
  });

  it('deduplicates repeated backend recommendations for the same twin state', async () => {
    renderProbe();

    fireEvent.click(screen.getByText('compute'));
    await screen.findByText('STU_BALANCED', { selector: '[data-testid="twin"]' });
    fireEvent.click(screen.getByText('recommend'));
    await screen.findByText('rec-1', { selector: '[data-testid="recommendation"]' });

    fireEvent.click(screen.getByText('more'));

    await screen.findByText('No additional recommendations available for this state.', { selector: '[data-testid="recommendation-message"]' });
    expect(screen.getByTestId('recommendations')).toHaveTextContent('1');
    expect(endpointMocks.recommend).toHaveBeenCalledTimes(2);
  });

  it('appends a distinct additional backend recommendation', async () => {
    endpointMocks.recommend
      .mockResolvedValueOnce(recommendation())
      .mockResolvedValueOnce(alternateRecommendation());
    renderProbe();

    fireEvent.click(screen.getByText('compute'));
    await screen.findByText('STU_BALANCED', { selector: '[data-testid="twin"]' });
    fireEvent.click(screen.getByText('recommend'));
    await screen.findByText('rec-1', { selector: '[data-testid="recommendation"]' });
    fireEvent.click(screen.getByText('more'));

    await screen.findByText('rec-2', { selector: '[data-testid="recommendation"]' });
    expect(screen.getByTestId('recommendations')).toHaveTextContent('2');
  });

  it('does not record a follow-up outcome for a rejected intervention decision', async () => {
    renderProbe();

    fireEvent.click(screen.getByText('compute'));
    await screen.findByText('STU_BALANCED', { selector: '[data-testid="twin"]' });
    fireEvent.click(screen.getByText('recommend'));
    await screen.findByText('rec-1', { selector: '[data-testid="recommendation"]' });
    fireEvent.click(screen.getByText('rejected'));
    await screen.findByText('rejected', { selector: '[data-testid="decision"]' });

    fireEvent.click(screen.getByText('followup'));

    expect(endpointMocks.followup).not.toHaveBeenCalled();
    expect(screen.getByTestId('followup')).toHaveTextContent('none');
  });
});

describe('health handling', () => {
  it('shows a healthy state when the backend and production model are available', async () => {
    endpointMocks.health.mockResolvedValueOnce(healthyStatus());

    render(
      <DemoProvider>
        <TopBar />
      </DemoProvider>,
    );

    expect(await screen.findByText('API ONLINE')).toBeInTheDocument();
  });

  it('shows a degraded state when the backend reports the model is unavailable', async () => {
    endpointMocks.health.mockResolvedValueOnce(healthyStatus({ model_loaded: false, production_model_available: false }));

    render(
      <DemoProvider>
        <TopBar />
      </DemoProvider>,
    );

    expect(await screen.findByText('API UNHEALTHY')).toBeInTheDocument();
  });
});
