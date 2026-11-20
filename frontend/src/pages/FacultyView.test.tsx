import { render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { DemoProvider } from '../context/DemoContext';
import type { StudentHistory, SystemAnalytics } from '../types';
import FacultyView from './FacultyView';

const endpointMocks = vi.hoisted(() => ({
  history: vi.fn(),
  analytics: vi.fn(),
}));

vi.mock('../api/endpoints', () => ({
  endpoints: endpointMocks,
}));

function history(overrides: Partial<StudentHistory> = {}): StudentHistory {
  return {
    student_id: 'STU_BALANCED',
    total_interventions: 1,
    acceptance_rate: 1,
    completion_rate: 0,
    success_rate: 0,
    interventions: [
      {
        intervention_id: 'int-accepted',
        student_id: 'STU_BALANCED',
        timestamp: '2026-09-15T00:00:00',
        scenario_id: 'rec-1',
        scenario_type: 'INCREASE_SLEEP',
        scenario_description: 'Improve sleep to 8 hours/night',
        baseline_risk: 0.7,
        counterfactual_risk: 0.55,
        predicted_risk_delta: 0.15,
        predicted_strain_delta: null,
        status: 'accepted',
        offered_at_day: 35,
        accepted_at_day: 35,
        completed_at_day: null,
        student_response: 'accepted',
        student_feedback: null,
        actual_risk_at_day7: null,
        actual_risk_delta: null,
        outcome_report_id: null,
        agent_diagnoses: [],
        recommendation_confidence: 'medium',
      },
    ],
    outcomes: [],
    ...overrides,
  };
}

function analytics(): SystemAnalytics {
  return {
    registry: {
      total_interventions: 1,
      acceptance_rate: 1,
      completion_rate: 0,
      effectiveness: {},
      by_scenario_type: {},
    },
    outcomes: {
      total_tracked: 0,
      success_rate: 0,
      prediction_accuracy: {},
    },
    supported_scenarios: {},
  };
}

beforeEach(() => {
  endpointMocks.history.mockResolvedValue(history());
  endpointMocks.analytics.mockResolvedValue(analytics());
});

afterEach(() => {
  endpointMocks.history.mockReset();
  endpointMocks.analytics.mockReset();
});

describe('FacultyView', () => {
  it('loads backend history and analytics for the selected demo student', async () => {
    render(
      <DemoProvider>
        <FacultyView />
      </DemoProvider>,
    );

    expect(endpointMocks.history).toHaveBeenCalledWith('STU_BALANCED', 35);
    expect(endpointMocks.analytics).toHaveBeenCalled();
    expect(await screen.findByText('Improve sleep to 8 hours/night')).toBeInTheDocument();
    expect(screen.getByText('Interventions Logged')).toBeInTheDocument();
  });

  it('shows an empty state when no student history exists yet', async () => {
    endpointMocks.history.mockResolvedValueOnce(history({
      total_interventions: 0,
      acceptance_rate: 0,
      success_rate: 0,
      interventions: [],
      outcomes: [],
    }));

    render(
      <DemoProvider>
        <FacultyView />
      </DemoProvider>,
    );

    expect(await screen.findByText('No intervention history is available for this student yet.')).toBeInTheDocument();
  });
});
