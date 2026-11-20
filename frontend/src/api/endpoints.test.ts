import { afterEach, describe, expect, it, vi } from 'vitest';
import type { Recommendation } from '../types';
import { apiFetch } from './client';
import { endpoints } from './endpoints';

vi.mock('./client', () => ({
  apiFetch: vi.fn(),
}));

const mockedApiFetch = vi.mocked(apiFetch);

function sampleRecommendation(): Recommendation {
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
    primary_diagnoses: ['RecoveryAgent: sleep_deficit'],
    confidence: 'medium',
    caveats: ['Trained on synthetic data only'],
    timestamp: '2026-09-11T00:00:00',
    student_id: 'STU_PHASE7',
    day: 50,
  };
}

afterEach(() => {
  mockedApiFetch.mockReset();
});

describe('endpoint contract boundary', () => {
  it('uses the frozen Phase 7 API paths for final demo endpoints', async () => {
    mockedApiFetch.mockResolvedValue({});

    await endpoints.modelMetadata();
    expect(mockedApiFetch).toHaveBeenLastCalledWith('/metadata/model');

    await endpoints.followup('int-1', { followup_day: 42, observations: [] });
    expect(mockedApiFetch).toHaveBeenLastCalledWith('/outcomes/int-1/followup', expect.objectContaining({
      method: 'POST',
    }));

    await endpoints.updateResponse('int-1', { response: 'ask_more', day: 35 });
    expect(mockedApiFetch).toHaveBeenLastCalledWith('/interventions/int-1/response', expect.objectContaining({
      method: 'PATCH',
    }));

    await endpoints.history('STU/QA 1');
    expect(mockedApiFetch).toHaveBeenLastCalledWith('/students/STU%2FQA%201/history');

    await endpoints.history('STU/QA 1', 50);
    expect(mockedApiFetch).toHaveBeenLastCalledWith('/students/STU%2FQA%201/history?day=50');

    await endpoints.analytics();
    expect(mockedApiFetch).toHaveBeenLastCalledWith('/analytics/system');
  });

  it('serializes intervention logging with the canonical backend shape', async () => {
    mockedApiFetch.mockResolvedValue({
      intervention_id: 'int-1',
      record: {},
      persistence_base: 'data/phase7',
    });

    await endpoints.logIntervention({
      recommendation: sampleRecommendation(),
      student_response: 'accepted',
      feedback: 'Confirmed',
    });

    expect(mockedApiFetch).toHaveBeenCalledWith('/interventions/log', expect.objectContaining({
      method: 'POST',
      body: expect.any(String),
    }));
    const [, init] = mockedApiFetch.mock.calls[0];
    const body = JSON.parse(String(init?.body)) as Record<string, unknown>;

    expect(body).toMatchObject({
      recommendation: expect.objectContaining({
        scenario_id: 'rec-1',
        student_id: 'STU_PHASE7',
        day: 50,
      }),
      student_response: 'accepted',
      feedback: 'Confirmed',
    });
    expect(body).not.toHaveProperty('student_id');
    expect(body).not.toHaveProperty('intervention_id');
    expect(body).not.toHaveProperty('response');
    expect(body.student_response).not.toBe('accept');
  });
});
