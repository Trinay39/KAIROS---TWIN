import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { StudentHistory as StudentHistoryType } from '../types';
import StudentHistory from './StudentHistory';

const endpointMocks = vi.hoisted(() => ({
  history: vi.fn(),
}));

vi.mock('../api/endpoints', () => ({
  endpoints: endpointMocks,
}));

vi.mock('../context/DemoContext', () => ({
  useDemo: () => ({
    state: {
      input: { student_id: 'STU_PRESSURE', day: 50, study_hours: 7.5, sleep_hours: 6.2, stress_level: 6, grade: 74, attendance_rate: 0.9, missed_deadline_observed: 0 },
    },
  }),
}));

function history(overrides: Partial<StudentHistoryType> = {}): StudentHistoryType {
  return {
    student_id: 'STU_PRESSURE',
    total_interventions: 0,
    acceptance_rate: 0,
    completion_rate: 0,
    success_rate: 0,
    interventions: [],
    outcomes: [],
    observations: [
      { day: 49, study_hours: 7.1, sleep_hours: 6, stress_level: 6, workload_pressure: 0.72, upcoming_deadlines_7d: 4, attendance_rate: 0.9, engagement_score: 0.55 },
      { day: 50, study_hours: 7.5, sleep_hours: 6.2, stress_level: 6, workload_pressure: 0.72, upcoming_deadlines_7d: 4, attendance_rate: 0.9, engagement_score: 0.55 },
    ],
    observation_summary: { available: true, current_day: 50, total_observations: 2, data_source: 'synthetic_demo_observation' },
    ...overrides,
  };
}

beforeEach(() => {
  endpointMocks.history.mockReset();
  endpointMocks.history.mockResolvedValue(history());
});

describe('StudentHistory', () => {
  it('loads selected-day observations and renders history sections', async () => {
    render(<StudentHistory />);

    expect(endpointMocks.history).toHaveBeenCalledWith('STU_PRESSURE', 50);
    expect(await screen.findByText('Behavioral Trajectory')).toBeInTheDocument();
    expect(screen.getByText('Recovery & Stress')).toBeInTheDocument();
    expect(screen.getByText('Academic Pressure')).toBeInTheDocument();
  });

  it('shows an empty observation state', async () => {
    endpointMocks.history.mockResolvedValueOnce(history({
      observations: [],
      observation_summary: { available: false, reason: 'No historical observations available.', current_day: 50 },
    }));

    render(<StudentHistory />);

    expect(await screen.findByText('No historical observations available.')).toBeInTheDocument();
  });
});
