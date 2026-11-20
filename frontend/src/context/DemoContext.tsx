import { createContext, useCallback, useContext, useRef, useState } from 'react';
import { messageForError, statusForError } from '../api/client';
import { endpoints } from '../api/endpoints';
import type {
  DiagnosticsResponse,
  FollowupOutcomeResponse,
  PredictionResponse,
  Recommendation,
  RecommendationDecision,
  RequestStatus,
  SimulationResponse,
  StudentTwinState,
} from '../types';

export interface StudentInput {
  student_id: string;
  day: number;
  study_hours: number;
  sleep_hours: number;
  stress_level: number;
  grade: number;
  attendance_rate: number;
  missed_deadline_observed: number;
}

type PipelineStep = 'input' | 'twin' | 'risk' | 'diag' | 'whatif' | 'rec' | 'decision' | 'followup';
type PipelineStatuses = Record<PipelineStep, RequestStatus>;

interface PipelineState {
  input: StudentInput;
  twin: StudentTwinState | null;
  prediction: PredictionResponse | null;
  diagnostics: DiagnosticsResponse | null;
  sim: SimulationResponse | null;
  rec: Recommendation | null;
  recommendations: Recommendation[];
  recommendationMessage: string | null;
  interventionId: string | null;
  decision: RecommendationDecision | null;
  followup: FollowupOutcomeResponse | null;
  status: PipelineStatuses;
  error: string | null;
}

const presets = {
  BALANCED: { student_id: 'STU_BALANCED', day: 35, study_hours: 6.5, sleep_hours: 8.0, stress_level: 2, grade: 86, attendance_rate: 0.95, missed_deadline_observed: 0 },
  ACADEMIC_PRESSURE: { student_id: 'STU_PRESSURE', day: 50, study_hours: 7.5, sleep_hours: 6.2, stress_level: 6, grade: 74, attendance_rate: 0.90, missed_deadline_observed: 0 },
  OVERLOADED: { student_id: 'STU_OVERLOADED', day: 50, study_hours: 2.5, sleep_hours: 5.0, stress_level: 9, grade: 55, attendance_rate: 0.70, missed_deadline_observed: 1 },
  RECOVERY: { student_id: 'STU_RECOVERY', day: 65, study_hours: 4.0, sleep_hours: 8.2, stress_level: 4, grade: 72, attendance_rate: 0.88, missed_deadline_observed: 0 },
  DEADLINE_CRUNCH: { student_id: 'STU_DEADLINE', day: 82, study_hours: 6.0, sleep_hours: 5.8, stress_level: 8, grade: 78, attendance_rate: 0.85, missed_deadline_observed: 1 },
};

export { presets };

const defaultInput: StudentInput = presets.BALANCED;

const pendingStatuses: PipelineStatuses = {
  input: 'done',
  twin: 'pending',
  risk: 'pending',
  diag: 'pending',
  whatif: 'pending',
  rec: 'pending',
  decision: 'pending',
  followup: 'pending',
};

const DemoContext = createContext<{
  state: PipelineState;
  presets: typeof presets;
  activePreset: string | null;
  applyScenario: (key: keyof typeof presets) => void;
  updateInput: (partial: Partial<StudentInput>) => void;
  resetToDefault: () => void;
  computeTwin: () => Promise<void>;
  predictRisk: () => Promise<void>;
  runDiagnostics: () => Promise<void>;
  runWhatIf: () => Promise<void>;
  generateRec: () => Promise<void>;
  generateMoreRec: () => Promise<void>;
  recordDecision: (a: RecommendationDecision) => Promise<void>;
  recordFollowup: () => Promise<void>;
} | null>(null);

function failedStatus(error: unknown): RequestStatus {
  return statusForError(error) as RequestStatus;
}

function clearDerivedState(state: PipelineState, input: StudentInput): PipelineState {
  return {
    ...state,
    input,
    twin: null,
    prediction: null,
    diagnostics: null,
    sim: null,
    rec: null,
    recommendations: [],
    recommendationMessage: null,
    interventionId: null,
    decision: null,
    followup: null,
    status: { ...pendingStatuses },
    error: null,
  };
}

function buildObservations(input: StudentInput) {
  const currentDay = input.day;
  const baseDay = Math.max(1, currentDay - 6);
  const history = [];

  const profiles: Record<string, number[][]> = {
    STU_DEMO: [[4.2, 7.8, 2], [4.5, 8.1, 2], [4.0, 7.9, 2], [4.8, 8.2, 2], [4.1, 7.7, 2], [4.3, 8.0, 2]],
    STU_BALANCED: [[4.2, 7.8, 2], [4.5, 8.1, 2], [4.0, 7.9, 2], [4.8, 8.2, 2], [4.1, 7.7, 2], [4.3, 8.0, 2]],
    STU_PRESSURE: [[6.8, 6.2, 5], [7.2, 6.0, 6], [7.0, 6.1, 5], [7.5, 5.9, 6], [6.9, 6.2, 5], [7.1, 6.0, 6]],
    STU_OVERLOADED: [[2.1, 4.8, 8], [2.8, 5.1, 9], [1.9, 4.9, 9], [2.3, 5.0, 8], [2.0, 4.7, 9], [2.6, 5.0, 9]],
    STU_RECOVERY: [[3.5, 8.3, 4], [3.8, 8.4, 4], [4.0, 8.2, 3], [4.1, 8.1, 3], [3.9, 8.3, 4], [4.0, 8.2, 3]],
    STU_DEADLINE: [[5.8, 5.9, 7], [6.2, 5.7, 7], [6.0, 5.8, 7], [6.1, 5.9, 8], [5.9, 5.8, 7], [6.0, 5.9, 8]],
  };

  const historicalValues = profiles[input.student_id] || profiles.STU_BALANCED;

  for (let i = 0; i < 6; i += 1) {
    const [studyHours, sleepHours, stressLevel] = historicalValues[i];
    history.push({
      day: baseDay + i,
      study_hours: studyHours,
      sleep_hours: sleepHours,
      stress_level: stressLevel,
      grade: input.grade - (6 - i) * 0.5,
      attendance_rate: input.attendance_rate,
      missed_deadline_observed: input.missed_deadline_observed,
    });
  }

  history.push({
    day: input.day,
    study_hours: input.study_hours,
    sleep_hours: input.sleep_hours,
    stress_level: input.stress_level,
    grade: input.grade,
    attendance_rate: input.attendance_rate,
    missed_deadline_observed: input.missed_deadline_observed,
  });

  return history;
}

export function DemoProvider({ children }: { children: React.ReactNode }) {
  const selectionVersion = useRef(0);
  const [activePreset, setActivePreset] = useState<string | null>(null);
  const [state, setState] = useState<PipelineState>({
    input: { ...defaultInput },
    twin: null,
    prediction: null,
    diagnostics: null,
    sim: null,
    rec: null,
    recommendations: [],
    recommendationMessage: null,
    interventionId: null,
    decision: null,
    followup: null,
    status: { ...pendingStatuses },
    error: null,
  });

  const invalidateSelection = useCallback(() => {
    selectionVersion.current += 1;
  }, []);

  const isCurrentSelection = useCallback((version: number, input: StudentInput) => {
    return (stateToCheck: PipelineState) =>
      selectionVersion.current === version &&
      stateToCheck.input.student_id === input.student_id &&
      stateToCheck.input.day === input.day;
  }, []);

  const updateInput = useCallback((partial: Partial<StudentInput>) => {
    invalidateSelection();
    setActivePreset(null);
    setState((s) => clearDerivedState(s, { ...s.input, ...partial }));
  }, [invalidateSelection]);

  const applyScenario = useCallback((key: keyof typeof presets) => {
    invalidateSelection();
    setActivePreset(key);
    setState((s) => clearDerivedState(s, { ...presets[key] }));
  }, [invalidateSelection]);

  const resetToDefault = useCallback(() => {
    invalidateSelection();
    setActivePreset(null);
    setState((s) => clearDerivedState(s, { ...defaultInput }));
  }, [invalidateSelection]);

  const computeTwin = useCallback(async () => {
    const input = { ...state.input };
    const observations = buildObservations(input);
    const requestVersion = selectionVersion.current;
    const isCurrent = isCurrentSelection(requestVersion, input);

    setState((s) => ({ ...s, status: { ...s.status, twin: 'loading' }, error: null }));
    try {
      const response = await endpoints.computeState({ student_id: input.student_id, day: input.day, observations });
      setState((s) => (
        isCurrent(s)
          ? { ...s, twin: response, prediction: null, diagnostics: null, sim: null, rec: null, recommendations: [], recommendationMessage: null, interventionId: null, decision: null, followup: null, status: { ...s.status, twin: 'done', risk: 'pending', diag: 'pending', whatif: 'pending', rec: 'pending', decision: 'pending', followup: 'pending' } }
          : s
      ));
    } catch (error) {
      setState((s) => (
        isCurrent(s)
          ? { ...s, error: messageForError(error, 'The selected student data could not be processed.'), status: { ...s.status, twin: failedStatus(error) } }
          : s
      ));
    }
  }, [isCurrentSelection, state.input]);

  const predictRisk = useCallback(async () => {
    if (!state.twin) {
      setState((s) => ({ ...s, error: 'Compute twin first' }));
      return;
    }
    const input = { ...state.input };
    const twin = state.twin;
    const requestVersion = selectionVersion.current;
    const isCurrent = isCurrentSelection(requestVersion, input);

    setState((s) => ({ ...s, status: { ...s.status, risk: 'loading' }, error: null }));
    try {
      const response = await endpoints.predict({ twin_state: twin, day: input.day });
      setState((s) => (
        isCurrent(s) ? { ...s, prediction: response, status: { ...s.status, risk: 'done' } } : s
      ));
    } catch (error) {
      setState((s) => (
        isCurrent(s)
          ? { ...s, error: messageForError(error, 'Prediction service is unavailable.'), status: { ...s.status, risk: failedStatus(error) } }
          : s
      ));
    }
  }, [isCurrentSelection, state.input, state.twin]);

  const runDiagnostics = useCallback(async () => {
    if (!state.twin) {
      setState((s) => ({ ...s, error: 'Compute twin first' }));
      return;
    }
    const input = { ...state.input };
    const twin = state.twin;
    const requestVersion = selectionVersion.current;
    const isCurrent = isCurrentSelection(requestVersion, input);

    setState((s) => ({ ...s, status: { ...s.status, diag: 'loading' }, error: null }));
    try {
      const response = await endpoints.diagnostics({ twin_state: twin, day: input.day });
      setState((s) => (
        isCurrent(s) ? { ...s, diagnostics: response, status: { ...s.status, diag: 'done' } } : s
      ));
    } catch (error) {
      setState((s) => (
        isCurrent(s)
          ? { ...s, error: messageForError(error, 'Diagnostics service is unavailable.'), status: { ...s.status, diag: failedStatus(error) } }
          : s
      ));
    }
  }, [isCurrentSelection, state.input, state.twin]);

  const runWhatIf = useCallback(async () => {
    if (!state.twin) {
      setState((s) => ({ ...s, error: 'Compute twin first' }));
      return;
    }
    const input = { ...state.input };
    const twin = state.twin;
    const requestVersion = selectionVersion.current;
    const isCurrent = isCurrentSelection(requestVersion, input);

    setState((s) => ({ ...s, status: { ...s.status, whatif: 'loading' }, error: null }));
    try {
      const scenarios = [
        { scenario_type: 'REDUCE_DEADLINE_DENSITY', description: 'Reduce deadline clustering', parameters: {}, scenario_id: 'sc-1' },
        { scenario_type: 'INCREASE_SLEEP', description: 'Improve sleep to 8 hours/night', parameters: { hours_per_night: 8.0 }, scenario_id: 'sc-2' },
        { scenario_type: 'INCREASE_STUDY_TIME', description: 'Add 1 hour/day study for 7 days', parameters: { hours_per_day: 1.0, days: 7 }, scenario_id: 'sc-3' },
        { scenario_type: 'REDUCE_WORKLOAD', description: 'Reduce workload by 20%', parameters: { reduction_pct: 20 }, scenario_id: 'sc-4' },
      ];
      const response = await endpoints.simulate({ twin_state: twin, day: input.day, scenarios });
      setState((s) => (
        isCurrent(s) ? { ...s, sim: response, status: { ...s.status, whatif: 'done' } } : s
      ));
    } catch (error) {
      setState((s) => (
        isCurrent(s)
          ? { ...s, error: messageForError(error, 'Simulation service is unavailable.'), status: { ...s.status, whatif: failedStatus(error) } }
          : s
      ));
    }
  }, [isCurrentSelection, state.input, state.twin]);

  const generateRec = useCallback(async () => {
    if (!state.twin) {
      setState((s) => ({ ...s, error: 'Compute twin first' }));
      return;
    }
    const input = { ...state.input };
    const twin = state.twin;
    const requestVersion = selectionVersion.current;
    const isCurrent = isCurrentSelection(requestVersion, input);

    setState((s) => ({ ...s, status: { ...s.status, rec: 'loading', decision: 'pending', followup: 'pending' }, error: null, recommendationMessage: null, interventionId: null, decision: null, followup: null }));
    try {
      const response = await endpoints.recommend({ twin_state: twin, day: input.day });
      setState((s) => (
        isCurrent(s) ? { ...s, rec: response, recommendations: [response], status: { ...s.status, rec: 'done' } } : s
      ));
    } catch (error) {
      setState((s) => (
        isCurrent(s)
          ? { ...s, error: messageForError(error, 'Recommendation service is unavailable.'), status: { ...s.status, rec: failedStatus(error) } }
          : s
      ));
    }
  }, [isCurrentSelection, state.input, state.twin]);

  const generateMoreRec = useCallback(async () => {
    if (!state.twin) {
      setState((s) => ({ ...s, error: 'Compute twin first' }));
      return;
    }
    if (state.status.rec === 'loading') return;
    const input = { ...state.input };
    const twin = state.twin;
    const requestVersion = selectionVersion.current;
    const isCurrent = isCurrentSelection(requestVersion, input);

    setState((s) => ({ ...s, status: { ...s.status, rec: 'loading' }, error: null, recommendationMessage: null }));
    try {
      const response = await endpoints.recommend({ twin_state: twin, day: input.day });
      setState((s) => {
        if (!isCurrent(s)) return s;
        const existing = s.recommendations.some((item) => item.scenario_id === response.scenario_id);
        if (existing) {
          return {
            ...s,
            recommendationMessage: 'No additional recommendations available for this state.',
            status: { ...s.status, rec: 'done' },
          };
        }
        return {
          ...s,
          rec: response,
          recommendations: [...s.recommendations, response],
          status: { ...s.status, rec: 'done' },
        };
      });
    } catch (error) {
      setState((s) => (
        isCurrent(s)
          ? { ...s, error: messageForError(error, 'Recommendation service is unavailable.'), status: { ...s.status, rec: failedStatus(error) } }
          : s
      ));
    }
  }, [isCurrentSelection, state.input, state.status.rec, state.twin]);

  const recordDecision = useCallback(async (action: RecommendationDecision) => {
    if (!state.rec) {
      setState((s) => ({ ...s, error: 'Generate recommendation first' }));
      return;
    }
    const input = { ...state.input };
    const recommendation = state.rec;
    const requestVersion = selectionVersion.current;
    const isCurrent = isCurrentSelection(requestVersion, input);

    setState((s) => ({ ...s, status: { ...s.status, decision: 'loading' }, error: null }));
    try {
      const log = await endpoints.logIntervention({
        recommendation,
        student_response: action,
      });
      setState((s) => (
        isCurrent(s)
          ? { ...s, interventionId: log.intervention_id, decision: action, followup: null, status: { ...s.status, decision: 'done', followup: 'pending' } }
          : s
      ));
    } catch (error) {
      setState((s) => (
        isCurrent(s)
          ? { ...s, error: messageForError(error, 'The intervention could not be recorded.'), status: { ...s.status, decision: failedStatus(error) } }
          : s
      ));
    }
  }, [isCurrentSelection, state.input, state.rec]);

  const recordFollowup = useCallback(async () => {
    if (!state.interventionId) {
      setState((s) => ({ ...s, error: 'Record an intervention decision first' }));
      return;
    }
    if (state.decision !== 'accepted') {
      setState((s) => ({ ...s, error: 'Follow-up outcome recording is available only after an accepted intervention.' }));
      return;
    }
    if (state.input.day > 83) {
      setState((s) => ({ ...s, error: 'Follow-up requires current day <= 83 so day+7 stays inside the semester.' }));
      return;
    }
    const input = { ...state.input };
    const interventionId = state.interventionId;
    const requestVersion = selectionVersion.current;
    const isCurrent = isCurrentSelection(requestVersion, input);
    const followupDay = input.day + 7;
    const observations = buildObservations({ ...input, day: followupDay });

    setState((s) => ({ ...s, status: { ...s.status, followup: 'loading' }, error: null }));
    try {
      const response = await endpoints.followup(interventionId, {
        followup_day: followupDay,
        observations,
        student_feedback: 'partial',
        student_feedback_text: 'Demo follow-up observation recorded from the current synthetic profile.',
      });
      setState((s) => (
        isCurrent(s)
          ? { ...s, followup: response, status: { ...s.status, followup: 'done' } }
          : s
      ));
    } catch (error) {
      setState((s) => (
        isCurrent(s)
          ? { ...s, error: messageForError(error, 'Follow-up outcome could not be recorded.'), status: { ...s.status, followup: failedStatus(error) } }
          : s
      ));
    }
  }, [isCurrentSelection, state.decision, state.input, state.interventionId]);

  const value = { state, presets, activePreset, applyScenario, updateInput, resetToDefault, computeTwin, predictRisk, runDiagnostics, runWhatIf, generateRec, generateMoreRec, recordDecision, recordFollowup };
  return <DemoContext.Provider value={value}>{children}</DemoContext.Provider>;
}

export function useDemo() {
  const ctx = useContext(DemoContext);
  if (!ctx) throw new Error('useDemo must be inside DemoProvider');
  return ctx;
}
