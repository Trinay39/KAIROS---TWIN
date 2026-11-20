"""
KAIROS-TWIN Phase 3: StudentTwinState schema.

This module defines the four-layer StudentTwinState that represents a student's
multi-dimensional state at a given point in time t. The state is computed only
from observations available at or before time t (no future information).

Follows Phase 1B frozen specification exactly.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class FieldProvenance:
    """Compact provenance record for a StudentTwinState field."""
    type: str
    source: str
    window: Optional[str] = None
    unit: Optional[str] = None
    formula_id: Optional[str] = None
    imputed: bool = False


@dataclass
class AcademicState:
    """Layer 2 (Derived): Academic performance and engagement indicators."""
    attendance_rate_7d: Optional[float] = None  # [0, 1]
    attendance_trend_7d: Optional[float] = None  # per day
    attendance_rate_30d: Optional[float] = None  # [0, 1]
    recent_grades_mean: Optional[float] = None  # [0, 1] normalized
    grade_trend_30d: Optional[float] = None  # OLS slope
    grades_below_personal_mean_pct: Optional[float] = None  # [0, 1]
    active_subjects_count: int = 0
    academic_load_score: Optional[float] = None  # [0, 1]
    missed_deadlines_14d: int = 0


@dataclass
class BehavioralState:
    """Layer 2 (Derived): Study and behavioral patterns."""
    avg_study_hours_3d: Optional[float] = None  # [0, 18]
    avg_study_hours_7d: Optional[float] = None
    avg_study_hours_14d: Optional[float] = None
    study_hours_trend_7d: Optional[float] = None  # hours/day
    study_variability_7d: Optional[float] = None  # [0, ∞)
    study_consistency_score: Optional[float] = None  # [0, 1]
    avg_session_duration_7d: Optional[float] = None  # hours/session
    break_rate_7d: Optional[float] = None  # breaks/hour
    distraction_rate_7d: Optional[float] = None  # per session
    focus_quality_7d_avg: Optional[float] = None  # [1, 5] Likert
    procrastination_index_7d: Optional[float] = None  # [0, 1]


@dataclass
class RecoveryState:
    """Layer 2 (Derived): Sleep and recovery indicators."""
    recovery_baseline_hours: float = 7.5  # configurable
    avg_sleep_hours_7d: Optional[float] = None  # [3, 12]
    avg_sleep_hours_14d: Optional[float] = None
    sleep_variability_7d: Optional[float] = None  # std dev
    sleep_deficit_7d_hours: Optional[float] = None  # [0, 49]
    sleep_debt_severity: Optional[float] = None  # [0, 1]
    rest_days_7d: int = 0  # [0, 7]
    recovery_ratio_7d: Optional[float] = None  # sleep/study
    recovery_score_7d: Optional[float] = None  # [0, 1]


@dataclass
class WorkloadState:
    """Layer 2 (Derived): Workload and deadline indicators."""
    deadline_schedule_published: bool = True
    pending_assignment_count: int = 0
    pending_assignment_effort_hours: Optional[float] = None
    deadline_density_next_7_known: Optional[int] = None  # future
    deadline_density_trend_7d: Optional[float] = None
    workload_pressure_score_7d: Optional[float] = None  # [0, 1]
    submission_rate_14d: Optional[float] = None  # [0, 1]
    submissions_on_time_pct_14d: Optional[float] = None
    effort_study_gap_7d: Optional[float] = None  # [-10, 10]


@dataclass
class EngagementState:
    """Layer 2 (Derived): Engagement and self-reported measures."""
    platform_interactions_7d_avg: Optional[float] = None  # [0, 200]
    interaction_trend_7d: Optional[float] = None
    interaction_engagement_score: Optional[float] = None  # [0, 1]
    avg_stress_7d: Optional[float] = None  # [1, 5] Likert, derived from internal [0, 1]
    stress_trend_7d: Optional[float] = None
    avg_confidence_7d: Optional[float] = None  # [1, 5]
    avg_wellbeing_7d: Optional[float] = None  # [1, 5]
    engagement_composite_score: Optional[float] = None  # [0, 1]


@dataclass
class TemporalContext:
    """Layer 2 (Derived): Temporal and calendar context."""
    day_of_semester: int = 1  # [1, 90]
    week_of_semester: int = 1  # [1, 13]
    day_of_week: int = 0  # [0, 6]
    is_exam_period: bool = False
    is_midterm_period: bool = False
    semester_phase: str = "early"  # "early", "mid", "late", "exam"
    days_until_exam_period: int = 90


@dataclass
class PredictionSnapshot:
    """Layer 3 (Predicted): ML model outputs at time t."""
    model_name: str = ""
    model_version: str = ""
    prediction_timestamp: Optional[datetime] = None
    overload_risk_probability: Optional[float] = None  # [0, 1]
    overload_label_binary: Optional[bool] = None
    threshold_applied: float = 0.5
    strain_index: Optional[float] = None  # [0, 1]
    feature_importances: Dict[str, float] = field(default_factory=dict)
    model_confidence: float = 0.5  # [0, 1]


@dataclass
class HistorySummary:
    """Layer 4 (Historical): Long-term summaries and trends."""
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


@dataclass
class StudentTwinState:
    """
    Four-layer student digital twin state at time t.

    Invariant: All fields in this state are computed from observations
    available at or before time t. No information from [t+1, t+90] is included.

    Layers:
    1. raw_latest: Mirror of today's observation (unmodified)
    2. Derived state: Academic, behavioral, recovery, workload, engagement, temporal
    3. Predictions: ML model outputs
    4. History: Long-term summaries
    """
    # Identifiers and metadata
    student_id: str = ""
    date: Optional[datetime] = None
    day: int = 1
    state_version: int = 0
    computed_at: Optional[datetime] = None
    data_source: str = "synthetic"  # "real", "synthetic", "pilot"

    # Layer 1: Raw Latest Observation
    raw_latest: Dict[str, Any] = field(default_factory=dict)

    # Layer 2: Derived State
    academic: AcademicState = field(default_factory=AcademicState)
    behavioral: BehavioralState = field(default_factory=BehavioralState)
    recovery: RecoveryState = field(default_factory=RecoveryState)
    workload: WorkloadState = field(default_factory=WorkloadState)
    engagement: EngagementState = field(default_factory=EngagementState)
    temporal: TemporalContext = field(default_factory=TemporalContext)

    # Layer 3: Predictions
    predictions: PredictionSnapshot = field(default_factory=PredictionSnapshot)

    # Layer 4: History
    history: HistorySummary = field(default_factory=HistorySummary)

    # Compact registry keyed by paths such as "academic.attendance_rate_7d".
    provenance: Dict[str, FieldProvenance] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert state to dictionary for serialization."""
        from dataclasses import asdict
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "StudentTwinState":
        """Reconstruct state from dictionary."""
        from dataclasses import fields as dc_fields

        field_types = {f.name: f.type for f in dc_fields(cls)}

        # Handle nested dataclasses
        if isinstance(d.get('academic'), dict):
            d['academic'] = AcademicState(**d['academic'])
        if isinstance(d.get('behavioral'), dict):
            d['behavioral'] = BehavioralState(**d['behavioral'])
        if isinstance(d.get('recovery'), dict):
            d['recovery'] = RecoveryState(**d['recovery'])
        if isinstance(d.get('workload'), dict):
            d['workload'] = WorkloadState(**d['workload'])
        if isinstance(d.get('engagement'), dict):
            d['engagement'] = EngagementState(**d['engagement'])
        if isinstance(d.get('temporal'), dict):
            d['temporal'] = TemporalContext(**d['temporal'])
        if isinstance(d.get('predictions'), dict):
            d['predictions'] = PredictionSnapshot(**d['predictions'])
        if isinstance(d.get('history'), dict):
            d['history'] = HistorySummary(**d['history'])
        if isinstance(d.get('provenance'), dict):
            d['provenance'] = {
                key: (value if isinstance(value, FieldProvenance) else FieldProvenance(**value))
                for key, value in d['provenance'].items()
            }

        return cls(**{k: v for k, v in d.items() if k in field_types})
