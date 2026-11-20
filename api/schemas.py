"""
Pydantic schemas for the Phase 7 API boundary.

These models intentionally mirror the existing internal dataclasses and provide
explicit conversion helpers. They do not compute StudentTwinState values; state
construction remains delegated to core.twin_engine.TwinEngine.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.schemas import (
    AcademicState,
    BehavioralState,
    EngagementState,
    FieldProvenance,
    HistorySummary,
    PredictionSnapshot as CorePredictionSnapshot,
    RecoveryState,
    StudentTwinState,
    TemporalContext,
    WorkloadState,
)
from intervention.recommendation import (
    Recommendation,
    RecommendationConfidence,
)
from simulation.scenario_schema import Scenario, ScenarioType


class APIModel(BaseModel):
    """Base model with strict unknown-field rejection at the API boundary."""

    model_config = ConfigDict(extra="forbid")


class FieldProvenanceModel(APIModel):
    type: str
    source: str
    window: Optional[str] = None
    unit: Optional[str] = None
    formula_id: Optional[str] = None
    imputed: bool = False

    def to_internal(self) -> FieldProvenance:
        return FieldProvenance(**self.model_dump())


class AcademicStateModel(APIModel):
    attendance_rate_7d: Optional[float] = None
    attendance_trend_7d: Optional[float] = None
    attendance_rate_30d: Optional[float] = None
    recent_grades_mean: Optional[float] = None
    grade_trend_30d: Optional[float] = None
    grades_below_personal_mean_pct: Optional[float] = None
    active_subjects_count: int = 0
    academic_load_score: Optional[float] = None
    missed_deadlines_14d: int = 0

    def to_internal(self) -> AcademicState:
        return AcademicState(**self.model_dump())


class BehavioralStateModel(APIModel):
    avg_study_hours_3d: Optional[float] = None
    avg_study_hours_7d: Optional[float] = None
    avg_study_hours_14d: Optional[float] = None
    study_hours_trend_7d: Optional[float] = None
    study_variability_7d: Optional[float] = None
    study_consistency_score: Optional[float] = None
    avg_session_duration_7d: Optional[float] = None
    break_rate_7d: Optional[float] = None
    distraction_rate_7d: Optional[float] = None
    focus_quality_7d_avg: Optional[float] = None
    procrastination_index_7d: Optional[float] = None

    def to_internal(self) -> BehavioralState:
        return BehavioralState(**self.model_dump())


class RecoveryStateModel(APIModel):
    recovery_baseline_hours: float = 7.5
    avg_sleep_hours_7d: Optional[float] = None
    avg_sleep_hours_14d: Optional[float] = None
    sleep_variability_7d: Optional[float] = None
    sleep_deficit_7d_hours: Optional[float] = None
    sleep_debt_severity: Optional[float] = None
    rest_days_7d: int = 0
    recovery_ratio_7d: Optional[float] = None
    recovery_score_7d: Optional[float] = None

    def to_internal(self) -> RecoveryState:
        return RecoveryState(**self.model_dump())


class WorkloadStateModel(APIModel):
    deadline_schedule_published: bool = True
    pending_assignment_count: int = 0
    pending_assignment_effort_hours: Optional[float] = None
    deadline_density_next_7_known: Optional[int] = None
    deadline_density_trend_7d: Optional[float] = None
    workload_pressure_score_7d: Optional[float] = None
    submission_rate_14d: Optional[float] = None
    submissions_on_time_pct_14d: Optional[float] = None
    effort_study_gap_7d: Optional[float] = None

    def to_internal(self) -> WorkloadState:
        return WorkloadState(**self.model_dump())


class EngagementStateModel(APIModel):
    platform_interactions_7d_avg: Optional[float] = None
    interaction_trend_7d: Optional[float] = None
    interaction_engagement_score: Optional[float] = None
    avg_stress_7d: Optional[float] = None
    stress_trend_7d: Optional[float] = None
    avg_confidence_7d: Optional[float] = None
    avg_wellbeing_7d: Optional[float] = None
    engagement_composite_score: Optional[float] = None

    def to_internal(self) -> EngagementState:
        return EngagementState(**self.model_dump())


class TemporalContextModel(APIModel):
    day_of_semester: int = 1
    week_of_semester: int = 1
    day_of_week: int = 0
    is_exam_period: bool = False
    is_midterm_period: bool = False
    semester_phase: str = "early"
    days_until_exam_period: int = 90

    def to_internal(self) -> TemporalContext:
        return TemporalContext(**self.model_dump())


class PredictionSnapshotModel(APIModel):
    model_name: str = ""
    model_version: str = ""
    prediction_timestamp: Optional[datetime] = None
    overload_risk_probability: Optional[float] = None
    overload_label_binary: Optional[bool] = None
    threshold_applied: float = 0.5
    strain_index: Optional[float] = None
    feature_importances: Dict[str, float] = Field(default_factory=dict)
    model_confidence: float = 0.5

    def to_internal(self) -> CorePredictionSnapshot:
        return CorePredictionSnapshot(**self.model_dump())


class HistorySummaryModel(APIModel):
    total_observations: int = 0
    observations_with_full_data: int = 0
    avg_overload_risk_30d: Optional[float] = None
    overload_risk_trend_30d: Optional[float] = None
    peak_overload_risk_30d: Optional[float] = None
    interventions_received_lifetime: int = 0
    interventions_accepted_lifetime: int = 0
    intervention_acceptance_rate: Optional[float] = None
    state_updates_count: int = 0
    days_with_high_stress_30d: int = 0
    days_with_sleep_deficit_30d: int = 0
    cohort_percentile_risk: Optional[float] = None

    def to_internal(self) -> HistorySummary:
        return HistorySummary(**self.model_dump())


class StudentTwinStateModel(APIModel):
    student_id: str = ""
    date: Optional[datetime] = None
    day: int = 1
    state_version: int = 0
    computed_at: Optional[datetime] = None
    data_source: str = "synthetic"
    raw_latest: Dict[str, Any] = Field(default_factory=dict)
    academic: AcademicStateModel = Field(default_factory=AcademicStateModel)
    behavioral: BehavioralStateModel = Field(default_factory=BehavioralStateModel)
    recovery: RecoveryStateModel = Field(default_factory=RecoveryStateModel)
    workload: WorkloadStateModel = Field(default_factory=WorkloadStateModel)
    engagement: EngagementStateModel = Field(default_factory=EngagementStateModel)
    temporal: TemporalContextModel = Field(default_factory=TemporalContextModel)
    predictions: PredictionSnapshotModel = Field(default_factory=PredictionSnapshotModel)
    history: HistorySummaryModel = Field(default_factory=HistorySummaryModel)
    provenance: Dict[str, FieldProvenanceModel] = Field(default_factory=dict)

    def to_internal(self) -> StudentTwinState:
        return StudentTwinState(
            student_id=self.student_id,
            date=self.date,
            day=self.day,
            state_version=self.state_version,
            computed_at=self.computed_at,
            data_source=self.data_source,
            raw_latest=self.raw_latest,
            academic=self.academic.to_internal(),
            behavioral=self.behavioral.to_internal(),
            recovery=self.recovery.to_internal(),
            workload=self.workload.to_internal(),
            engagement=self.engagement.to_internal(),
            temporal=self.temporal.to_internal(),
            predictions=self.predictions.to_internal(),
            history=self.history.to_internal(),
            provenance={key: value.to_internal() for key, value in self.provenance.items()},
        )

    @classmethod
    def from_internal(cls, state: StudentTwinState) -> "StudentTwinStateModel":
        return cls.model_validate(state.to_dict())


class ComputeStateRequest(APIModel):
    student_id: str
    day: int = Field(..., ge=1, le=90)
    observations: List[Dict[str, Any]]
    data_source: str = "synthetic"

    @field_validator("observations")
    @classmethod
    def observations_must_not_be_empty(cls, value: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not value:
            raise ValueError("observations must not be empty")
        return value


class StateRequest(APIModel):
    twin_state: StudentTwinStateModel
    day: int = Field(..., ge=1, le=90)


class ScenarioPayload(APIModel):
    scenario_id: Optional[str] = None
    scenario_type: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    affected_state_variables: List[str] = Field(default_factory=list)
    feasibility_metadata: Dict[str, Any] = Field(default_factory=dict)
    human_readable_explanation: str = ""

    @field_validator("scenario_type")
    @classmethod
    def supported_scenario_type(cls, value: str) -> str:
        normalized = value.upper()
        lower_values = {member.value for member in ScenarioType}
        if normalized not in ScenarioType.__members__ and value not in lower_values:
            raise ValueError(f"unsupported scenario_type: {value}")
        return value

    @classmethod
    def from_internal(cls, scenario: Scenario) -> "ScenarioPayload":
        return cls(
            scenario_id=scenario.scenario_id,
            scenario_type=scenario.scenario_type.value,
            description=scenario.description,
            parameters=scenario.parameters,
            affected_state_variables=scenario.affected_state_variables,
            feasibility_metadata=scenario.feasibility_metadata,
            human_readable_explanation=scenario.human_readable_explanation,
        )


class GenerateScenariosRequest(StateRequest):
    include_all: bool = False


class SimulationRequest(StateRequest):
    scenarios: Optional[List[ScenarioPayload]] = None
    include_all_if_empty: bool = False


class RecommendationRequest(StateRequest):
    pass


class RecommendationPayload(APIModel):
    scenario_id: str
    scenario_type: str
    scenario_description: str
    baseline_risk: float
    counterfactual_risk: float
    risk_delta: float
    risk_reduction_percentage: float
    strain_delta: Optional[float] = None
    changed_features_count: int = 0
    top_changed_features: List[Dict[str, Any]] = Field(default_factory=list)
    explanation: str = ""
    primary_diagnoses: List[str] = Field(default_factory=list)
    confidence: str = "medium"
    caveats: List[str] = Field(default_factory=list)
    timestamp: Optional[str] = None
    student_id: str = ""
    day: int = 0

    def to_internal(self) -> Recommendation:
        from intervention.recommendation import RecommendationConfidence
        confidence = RecommendationConfidence(self.confidence)
        kwargs = self.model_dump(exclude={"timestamp"})
        kwargs["confidence"] = confidence
        return Recommendation(**kwargs)

    @classmethod
    def from_internal(cls, recommendation: Recommendation) -> "RecommendationPayload":
        data = recommendation.to_dict()
        data.pop("was_successful", None)
        return cls(**data)


class LogInterventionRequest(APIModel):
    recommendation: RecommendationPayload
    student_response: Optional[str] = None
    feedback: Optional[str] = None


class UpdateResponseRequest(APIModel):
    response: str
    day: int = Field(..., ge=1, le=90)
    feedback: Optional[str] = None


class FollowupOutcomeRequest(APIModel):
    followup_day: int = Field(..., ge=1, le=90)
    observations: List[Dict[str, Any]]
    student_feedback: Optional[str] = None
    student_feedback_text: Optional[str] = None

    @field_validator("observations")
    @classmethod
    def followup_observations_must_not_be_empty(cls, value: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not value:
            raise ValueError("observations must not be empty")
        return value


class ErrorResponse(APIModel):
    detail: str
