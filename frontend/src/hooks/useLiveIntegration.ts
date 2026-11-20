import { useState, useEffect, useCallback } from 'react';
import { messageForError } from '../api/client';
import { endpoints } from '../api/endpoints';
import type { StudentTwinState, SimulationRequest, Recommendation, HealthStatus, PredictionResponse } from '../types';

export interface LiveState {
  twin?: StudentTwinState | null;
  prediction?: PredictionResponse | null;
  diagnostics?: { diagnoses: Record<string, unknown[]>; statistics: unknown } | null;
  recommendation?: Recommendation | null;
  simulation?: unknown | null;
  health?: HealthStatus | null;
  loading: boolean;
  error: string | null;
}

const DEMO_OBS: Record<string, Record<string, unknown>[]> = {
  stable: [{ day: 50, study_hours: 4.5, sleep_hours: 7.2, stress_level: 3.0, grade: 78, attendance_rate: 0.92, missed_deadline_observed: 0, workload_score: 0.55, recovery_score: 0.78 }],
  deadline: [{ day: 50, study_hours: 6.8, sleep_hours: 4.1, stress_level: 8.5, grade: 62, attendance_rate: 0.75, missed_deadline_observed: 1, workload_score: 0.92, recovery_score: 0.22 }],
  recovery: [{ day: 50, study_hours: 3.2, sleep_hours: 3.8, stress_level: 9.4, grade: 55, attendance_rate: 0.68, missed_deadline_observed: 2, workload_score: 0.88, recovery_score: 0.15 }],
  emerging: [{ day: 50, study_hours: 5.2, sleep_hours: 5.8, stress_level: 5.5, grade: 72, attendance_rate: 0.85, missed_deadline_observed: 0, workload_score: 0.72, recovery_score: 0.45 }],
};

export function useLiveIntegration(demoKey: string) {
  const [state, setState] = useState<LiveState>({ loading: true, error: null });

  const fetchHealth = useCallback(async () => {
    try {
      const h = await endpoints.health();
      setState((s) => ({ ...s, health: h }));
    } catch {
      // health check failure is non-fatal
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 10000);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  useEffect(() => {
    let cancelled = false;
    const obs = DEMO_OBS[demoKey] ?? DEMO_OBS.stable;
    const studentId = 'STU_DEMO';
    const day = 50;

    async function load() {
      setState((s) => ({ ...s, loading: true, error: null }));
      try {
        const twin = await endpoints.computeState({ student_id: studentId, day, observations: obs });
        if (cancelled) return;
        const pred = await endpoints.predict({ twin_state: twin, day });
        if (cancelled) return;
        const diag = await endpoints.diagnostics({ twin_state: twin, day });
        if (cancelled) return;
        setState((s) => ({ ...s, twin, prediction: pred, diagnostics: diag, recommendation: null, simulation: null, loading: false, error: null }));
      } catch (e: unknown) {
        if (!cancelled) setState((s) => ({ ...s, loading: false, error: messageForError(e, 'API unavailable') }));
      }
    }
    load();
    return () => { cancelled = true; };
  }, [demoKey]);

  const runSimulation = useCallback(async (scenarioType = 'INCREASE_SLEEP', twinState?: StudentTwinState | null) => {
    const twin = twinState ?? state.twin;
    if (!twin) return;
    setState((s) => ({ ...s, loading: true }));
    try {
      const req: SimulationRequest = {
        twin_state: twin,
        day: twin.day,
        scenarios: [{ scenario_type: scenarioType, parameters: { hours_per_night: 8.0 } }],
      };
      const res = await endpoints.simulate(req);
      setState((s) => ({ ...s, simulation: res, loading: false }));
    } catch (e: unknown) {
      setState((s) => ({ ...s, loading: false, error: messageForError(e, 'Simulation failed') }));
    }
  }, [state.twin]);

  const getRecommendation = useCallback(async () => {
    const twin = state.twin;
    if (!twin) return;
    setState((s) => ({ ...s, loading: true }));
    try {
      const rec = await endpoints.recommend({ twin_state: twin, day: twin.day || 50 });
      setState((s) => ({ ...s, recommendation: rec, loading: false }));
    } catch (e: unknown) {
      setState((s) => ({ ...s, loading: false, error: messageForError(e, 'Recommendations unavailable') }));
    }
  }, [state.twin]);

  return { ...state, runSimulation, getRecommendation };
}
