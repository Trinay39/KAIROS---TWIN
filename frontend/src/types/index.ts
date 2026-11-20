// Core domain types matching Phase 7 API schemas
export interface AcademicState {
  attendance_rate_7d: number | null;
  attendance_trend_7d: number | null;
  attendance_rate_30d: number | null;
  recent_grades_mean: number | null;
  grade_trend_30d: number | null;
  grades_below_personal_mean_pct: number | null;
  active_subjects_count: number;
  academic_load_score: number | null;
  missed_deadlines_14d: number;
}

export interface BehavioralState {
  avg_study_hours_3d: number | null;
  avg_study_hours_7d: number | null;
  avg_study_hours_14d: number | null;
  study_hours_trend_7d: number | null;
  study_variability_7d: number | null;
  study_consistency_score: number | null;
  avg_session_duration_7d: number | null;
  break_rate_7d: number | null;
  distraction_rate_7d: number | null;
  focus_quality_7d_avg: number | null;
  procrastination_index_7d: number | null;
}

export interface RecoveryState {
  recovery_baseline_hours: number;
  avg_sleep_hours_7d: number | null;
  avg_sleep_hours_14d: number | null;
  sleep_variability_7d: number | null;
  sleep_deficit_7d_hours: number | null;
  sleep_debt_severity: number | null;
  rest_days_7d: number;
  recovery_ratio_7d: number | null;
  recovery_score_7d: number | null;
}

export interface WorkloadState {
  deadline_schedule_published: boolean;
  pending_assignment_count: number;
  pending_assignment_effort_hours: number | null;
  deadline_density_next_7_known: number | null;
  deadline_density_trend_7d: number | null;
  workload_pressure_score_7d: number | null;
  submission_rate_14d: number | null;
  submissions_on_time_pct_14d: number | null;
  effort_study_gap_7d: number | null;
}

export interface EngagementState {
  platform_interactions_7d_avg: number | null;
  interaction_trend_7d: number | null;
  interaction_engagement_score: number | null;
  avg_stress_7d: number | null;
  stress_trend_7d: number | null;
  avg_confidence_7d: number | null;
  avg_wellbeing_7d: number | null;
  engagement_composite_score: number | null;
}

export interface FieldProvenance {
  type: 'observed' | 'derived' | 'imputed_default' | 'hardcoded' | 'predicted';
  source: string;
  window: string | null;
  unit: string | null;
  formula_id: string | null;
  imputed: boolean;
}

export interface TemporalContext {
  day_of_semester: number;
  week_of_semester: number;
  day_of_week: number;
  is_exam_period: boolean;
  is_midterm_period: boolean;
  semester_phase: string;
  days_until_exam_period: number;
}

export interface PredictionSnapshot {
  model_name: string;
  model_version: string;
  prediction_timestamp: string | null;
  overload_risk_probability: number | null;
  overload_label_binary: boolean | null;
  threshold_applied: number;
  strain_index: number | null;
  feature_importances: Record<string, number>;
  model_confidence: number;
}

export interface HistorySummary {
  total_observations: number;
  observations_with_full_data: number;
  avg_overload_risk_30d: number | null;
  overload_risk_trend_30d: number | null;
  peak_overload_risk_30d: number | null;
  interventions_received_lifetime: number;
  interventions_accepted_lifetime: number;
  intervention_acceptance_rate: number | null;
  state_updates_count: number;
  days_with_high_stress_30d: number;
  days_with_sleep_deficit_30d: number;
  cohort_percentile_risk: number | null;
}

export interface StudentTwinState {
  student_id: string;
  date: string | null;
  day: number;
  state_version: number;
  computed_at: string | null;
  data_source: string;
  raw_latest: Record<string, unknown>;
  academic: AcademicState;
  behavioral: BehavioralState;
  recovery: RecoveryState;
  workload: WorkloadState;
  engagement: EngagementState;
  temporal: TemporalContext;
  predictions: PredictionSnapshot;
  history: HistorySummary;
  provenance?: Record<string, FieldProvenance>;
}

export interface ComputeStateRequest {
  student_id: string;
  day: number;
  observations: Record<string, unknown>[];
  data_source?: string;
}

export interface ScenarioPayload {
  scenario_id?: string;
  scenario_type: string;
  description?: string;
  parameters: Record<string, unknown>;
  affected_state_variables?: string[];
  feasibility_metadata?: Record<string, unknown>;
  human_readable_explanation?: string;
}

export interface SimulationRequest {
  twin_state: StudentTwinState;
  day: number;
  scenarios?: ScenarioPayload[];
  include_all_if_empty?: boolean;
}

export interface GenerateScenariosRequest extends StateRequest {
  include_all?: boolean;
}

export interface CounterfactualResult {
  scenario_id: string;
  scenario_type: string;
  scenario_description: string;
  baseline_probability: number;
  counterfactual_probability: number;
  risk_delta: number;
  risk_reduction_percentage: number;
  baseline_strain: number | null;
  counterfactual_strain: number | null;
  strain_delta: number | null;
  changed_features_count: number;
  unchanged_features_count: number;
  interpretation: string;
}

export interface RankedScenario {
  rank: number;
  scenario_id: string;
  scenario_description: string;
  overall_score: number;
  risk_reduction_component: number;
  strain_reduction_component: number;
  feasibility_component: number;
  baseline_risk: number;
  counterfactual_risk: number;
  estimated_risk_reduction_pct: number;
}

export interface SimulationResponse {
  student_id: string;
  day: number;
  results: CounterfactualResult[];
  ranked_scenarios: RankedScenario[];
}

export interface Recommendation {
  scenario_id: string;
  scenario_type: string;
  scenario_description: string;
  baseline_risk: number;
  counterfactual_risk: number;
  risk_delta: number;
  risk_reduction_percentage: number;
  strain_delta: number | null;
  changed_features_count: number;
  top_changed_features: unknown[];
  explanation: string;
  primary_diagnoses: string[];
  confidence: string;
  caveats: string[];
  timestamp: string | null;
  student_id: string;
  day: number;
}

export type RecommendationDecision = 'accepted' | 'rejected' | 'deferred' | 'ask_more';

export interface Diagnosis {
  issue_name: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  affected_fields: string[];
  suggested_scenario_types: string[];
  confidence: number;
}

export interface DiagnosticsResponse {
  student_id: string;
  day: number;
  diagnoses: Record<string, Diagnosis[]>;
  statistics: {
    total_diagnoses: number;
    by_severity: Record<string, number>;
    by_agent: Record<string, number>;
    top_issues: Array<{
      agent: string;
      issue: string;
      severity: string;
      description: string;
    }>;
  };
}

export interface InterventionRegistryRecord {
  intervention_id: string;
  student_id: string;
  timestamp: string;
  scenario_id: string;
  scenario_type: string;
  scenario_description: string;
  baseline_risk: number;
  counterfactual_risk: number;
  predicted_risk_delta: number;
  predicted_strain_delta: number | null;
  status: string;
  offered_at_day: number;
  accepted_at_day: number | null;
  completed_at_day: number | null;
  student_response: RecommendationDecision | null;
  student_feedback: string | null;
  actual_risk_at_day7: number | null;
  actual_risk_delta: number | null;
  outcome_report_id: string | null;
  agent_diagnoses: string[];
  recommendation_confidence: string;
}

export interface InterventionLog {
  intervention_id: string;
  record: InterventionRegistryRecord;
  persistence_base: string;
}

export interface InterventionOutcome {
  outcome_id: string;
  intervention_id: string;
  student_id: string;
  timestamp: string;
  baseline_day: number;
  baseline_risk: number;
  baseline_strain: number | null;
  predicted_risk_delta: number;
  predicted_strain_delta: number | null;
  predicted_counterfactual_risk: number;
  followup_day: number;
  actual_risk_at_day7: number;
  actual_risk_delta: number;
  actual_strain_at_day7: number | null;
  actual_strain_delta: number | null;
  state_changes: Record<string, unknown>;
  student_self_report: string | null;
  student_feedback_text: string | null;
  was_successful: boolean;
  prediction_accuracy: number | null;
  confidence: number;
}

export interface FollowupOutcomeResponse {
  outcome_id: string;
  report: InterventionOutcome;
  record: InterventionRegistryRecord;
}

export interface StudentHistory {
  student_id: string;
  total_interventions: number;
  acceptance_rate: number;
  completion_rate: number;
  success_rate: number;
  interventions: InterventionRegistryRecord[];
  outcomes: unknown[];
  observations?: StudentHistoryObservation[];
  observation_summary?: {
    available: boolean;
    reason?: string;
    current_day?: number;
    total_observations?: number;
    data_source?: string;
  };
}

export interface StudentHistoryObservation {
  day: number;
  study_hours?: number;
  sleep_hours?: number;
  stress_level?: number;
  grade?: number;
  attendance_rate?: number;
  missed_deadline_observed?: number;
  pending_assignments?: number;
  upcoming_deadlines_7d?: number;
  workload_pressure?: number;
  engagement_score?: number;
  platform_interactions?: number;
}

export interface SystemAnalytics {
  registry: {
    total_interventions: number;
    acceptance_rate: number;
    completion_rate: number;
    effectiveness: Record<string, unknown>;
    by_scenario_type: Record<string, unknown>;
  };
  outcomes: {
    total_tracked: number;
    success_rate: number;
    prediction_accuracy: Record<string, unknown>;
  };
  supported_scenarios: Record<string, string[]>;
}

export interface ModelMetadata {
  model_name: string;
  model_type: string;
  is_loaded: boolean;
  has_regressor: boolean;
  num_features: number;
  feature_order: string[];
  threshold: number;
  threshold_source?: string;
  calibrated: boolean;
  calibration_method?: string | null;
  artifact_type?: string;
  probability_source: string;
  production_model_available: boolean;
  retraining_available: boolean;
  model_artifact?: string;
}

export interface HealthStatus {
  status: string;
  phase: string;
  prototype: boolean;
  model_loaded: boolean;
  production_model_available: boolean;
  calibrated: boolean;
  persistence_base: string;
  timestamp: string;
}

export interface StateRequest {
  twin_state: StudentTwinState;
  day: number;
}

export interface PredictionResponse {
  overload_probability: number;
  overload_prediction: boolean;
  strain_index: number | null;
  model_name: string;
  model_version: string;
  timestamp: string;
  day: number;
  top_contributing_features: Record<string, number>;
  confidence_info: Record<string, unknown> & {
    feature_importance_scope?: string;
    local_explanation_available?: boolean;
  };
}

export interface LogInterventionRequest {
  recommendation: Recommendation;
  student_response?: RecommendationDecision;
  feedback?: string;
}

export interface UpdateResponseRequest {
  response: RecommendationDecision;
  day: number;
  feedback?: string;
}

export interface FollowupOutcomeRequest {
  followup_day: number;
  observations: Record<string, unknown>[];
  student_feedback?: 'helped' | 'no_change' | 'worse' | 'partial';
  student_feedback_text?: string;
}

export type RequestStatus =
  | 'pending'
  | 'loading'
  | 'done'
  | 'validation_error'
  | 'auth_error'
  | 'server_error'
  | 'network_error'
  | 'error';

export function isFailureStatus(status: RequestStatus): boolean {
  return status.endsWith('_error') || status === 'error';
}

export type RiskLevel = 'low' | 'moderate' | 'high' | 'critical';

export function getRiskLevel(probability: number): RiskLevel {
  if (probability >= 0.75) return 'critical';
  if (probability >= 0.50) return 'high';
  if (probability >= 0.30) return 'moderate';
  return 'low';
}

export function getRiskColor(level: RiskLevel): string {
  switch (level) {
    case 'critical': return '#e0606e';
    case 'high': return '#f0a500';
    case 'moderate': return '#00bfa5';
    case 'low': return '#4ade80';
  }
}
