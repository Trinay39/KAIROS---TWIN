import { apiFetch } from './client';
import type {
  HealthStatus, ModelMetadata, StudentTwinState, ComputeStateRequest,
  StateRequest, SimulationRequest, Recommendation, LogInterventionRequest,
  UpdateResponseRequest, FollowupOutcomeRequest, StudentHistory, SystemAnalytics,
  DiagnosticsResponse, SimulationResponse, PredictionResponse, GenerateScenariosRequest,
  InterventionLog, FollowupOutcomeResponse, InterventionRegistryRecord,
} from '../types';

export const endpoints = {
  health: () => apiFetch<HealthStatus>('/health'),
  modelMetadata: () => apiFetch<ModelMetadata>('/metadata/model'),
  computeState: (payload: ComputeStateRequest) => apiFetch<StudentTwinState>('/states/compute', { method: 'POST', body: JSON.stringify(payload) }),
  predict: (payload: StateRequest) => apiFetch<PredictionResponse>('/predictions', { method: 'POST', body: JSON.stringify(payload) }),
  diagnostics: (payload: StateRequest) => apiFetch<DiagnosticsResponse>('/diagnostics', { method: 'POST', body: JSON.stringify(payload) }),
  scenarios: (payload: GenerateScenariosRequest) => apiFetch<{ student_id: string; day: number; scenarios: unknown[] }>('/scenarios/generate', { method: 'POST', body: JSON.stringify(payload) }),
  simulate: (payload: SimulationRequest) => apiFetch<SimulationResponse>('/simulations/run', { method: 'POST', body: JSON.stringify(payload) }),
  recommend: (payload: StateRequest) => apiFetch<Recommendation>('/recommendations/generate', { method: 'POST', body: JSON.stringify(payload) }),
  logIntervention: (payload: LogInterventionRequest) => apiFetch<InterventionLog>('/interventions/log', { method: 'POST', body: JSON.stringify(payload) }),
  updateResponse: (id: string, payload: UpdateResponseRequest) => apiFetch<{ intervention_id: string; record: InterventionRegistryRecord }>(`/interventions/${encodeURIComponent(id)}/response`, { method: 'PATCH', body: JSON.stringify(payload) }),
  followup: (id: string, payload: FollowupOutcomeRequest) => apiFetch<FollowupOutcomeResponse>(`/outcomes/${encodeURIComponent(id)}/followup`, { method: 'POST', body: JSON.stringify(payload) }),
  history: (studentId: string, day?: number) => apiFetch<StudentHistory>(`/students/${encodeURIComponent(studentId)}/history${day == null ? '' : `?day=${encodeURIComponent(day)}`}`),
  analytics: () => apiFetch<SystemAnalytics>('/analytics/system'),
};
