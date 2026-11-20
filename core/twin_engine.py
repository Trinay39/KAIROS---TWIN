"""
KAIROS-TWIN Phase 3: Twin State Engine.

Computes StudentTwinState(t) from observations available at or before day t.
All derived statistics use only data from [day 1, day t].

Key principle: TwinState(t) contains ZERO information from [t+1, t+90].
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, Tuple
import numpy as np
import pandas as pd
from core.schemas import (
    StudentTwinState, AcademicState, BehavioralState, RecoveryState,
    WorkloadState, EngagementState, TemporalContext, HistorySummary,
    FieldProvenance,
)


class TwinEngine:
    """Computes StudentTwinState from historical observations."""

    def __init__(self, baseline_sleep: float = 7.5):
        """
        Initialize twin engine.

        Args:
            baseline_sleep: Configurable recovery baseline (hours)
        """
        self.baseline_sleep = baseline_sleep

    def compute_state(
        self,
        student_id: str,
        day: int,
        student_df: pd.DataFrame,
        data_source: str = "synthetic"
    ) -> StudentTwinState:
        """
        Compute StudentTwinState at day t.

        Args:
            student_id: Student identifier
            day: Day of semester [1, 90]
            student_df: DataFrame with all observations for this student,
                       filtered to days [1, day] (NOT including future days)
            data_source: "real", "synthetic", or "pilot"

        Returns:
            StudentTwinState(t)

        Invariant:
            - All rolling statistics computed from observations in [1, t]
            - No future information (day > t) is accessed
        """
        # Ensure data is sorted and filtered to day t only
        obs_up_to_t = student_df[student_df['day'] <= day].sort_values('day')
        if len(obs_up_to_t) == 0:
            raise ValueError(f"No observations found for student {student_id} up to day {day}")

        today_obs = obs_up_to_t[obs_up_to_t['day'] == day]
        if len(today_obs) == 0:
            raise ValueError(f"No observation for student {student_id} on day {day}")
        today_obs = today_obs.iloc[0]

        # Initialize state
        state = StudentTwinState(
            student_id=str(student_id),
            day=int(day),
            date=datetime(2024, 9, 1) + pd.Timedelta(days=day-1),
            state_version=1,
            computed_at=datetime.now(),
            data_source=data_source,
            raw_latest=today_obs.to_dict()
        )

        self._validate_internal_stress(obs_up_to_t)

        # Compute Layer 2: Derived State
        state.workload = self._compute_workload(obs_up_to_t, today_obs)
        state.academic = self._compute_academic(obs_up_to_t, state.workload)
        state.behavioral = self._compute_behavioral(obs_up_to_t)
        state.recovery = self._compute_recovery(obs_up_to_t)
        state.engagement = self._compute_engagement(obs_up_to_t)
        state.temporal = self._compute_temporal(day)
        state.history = self._compute_history(obs_up_to_t)
        state.provenance = self._build_provenance(state, obs_up_to_t, today_obs)

        return state

    def _compute_academic(self, obs_up_to_t: pd.DataFrame, workload: WorkloadState) -> AcademicState:
        """Compute academic state from historical observations."""
        state = AcademicState()

        # Attendance rate (7-day and 30-day)
        if len(obs_up_to_t) >= 3:
            last_7 = obs_up_to_t.tail(7)
            if 'attendance_rate' in last_7.columns:
                valid_att = last_7['attendance_rate'].dropna()
                if len(valid_att) > 0:
                    state.attendance_rate_7d = float(valid_att.mean())
                if len(valid_att) > 1:
                    state.attendance_trend_7d = self._ols_slope(valid_att.values)

            last_30 = obs_up_to_t.tail(30)
            if 'attendance_rate' in last_30.columns:
                valid_att_30 = last_30['attendance_rate'].dropna()
                if len(valid_att_30) > 0:
                    state.attendance_rate_30d = float(valid_att_30.mean())

        # Grade statistics
        if 'grade' in obs_up_to_t.columns:
            valid_grades = obs_up_to_t['grade'].dropna()
            if len(valid_grades) >= 3:
                # Recent mean
                recent_5 = valid_grades.tail(5)
                if len(recent_5) >= 3:
                    state.recent_grades_mean = float(recent_5.mean() / 100.0)  # normalize to [0,1]

                    # Grade trend (OLS slope)
                    if len(recent_5) > 1:
                        x = np.arange(len(recent_5))
                        y = recent_5.values
                        slope = np.polyfit(x, y, 1)[0] / 100.0  # normalize
                        state.grade_trend_30d = float(slope)

                prior_grades = valid_grades.iloc[:-len(recent_5)]
                if len(prior_grades) >= 3 and len(recent_5) >= 3:
                    personal_baseline = float(prior_grades.mean())
                    state.grades_below_personal_mean_pct = float(
                        (recent_5 < personal_baseline).mean()
                    )

        # Missed deadlines in [day-14, day]
        if 'missed_deadline_observed' in obs_up_to_t.columns:
            last_14 = obs_up_to_t.tail(14)
            state.missed_deadlines_14d = int(last_14['missed_deadline_observed'].sum())

        subject_cols = [c for c in ["subject_id", "course_id", "subject", "course"] if c in obs_up_to_t.columns]
        if subject_cols:
            active_subjects = obs_up_to_t.tail(30)[subject_cols[0]].dropna().nunique()
            state.active_subjects_count = int(active_subjects)

        state.academic_load_score = self._compute_academic_load_score(obs_up_to_t, workload)
        return state

    def _compute_behavioral(self, obs_up_to_t: pd.DataFrame) -> BehavioralState:
        """Compute behavioral state from study patterns."""
        state = BehavioralState()

        if 'study_hours' in obs_up_to_t.columns:
            # 3-day, 7-day, 14-day averages
            last_3 = obs_up_to_t.tail(3)['study_hours'].dropna()
            if len(last_3) > 0:
                state.avg_study_hours_3d = float(last_3.mean())

            last_7 = obs_up_to_t.tail(7)['study_hours'].dropna()
            if len(last_7) > 0:
                state.avg_study_hours_7d = float(last_7.mean())

                # Study variability
                if len(last_7) > 1:
                    std_study = float(last_7.std())
                    mean_study = float(last_7.mean())
                    if mean_study > 0:
                        state.study_variability_7d = std_study / (mean_study + 0.1)
                        state.study_consistency_score = float(1.0 - min(1.0, state.study_variability_7d / 2.0))

                    # Study trend
                    if len(last_7) > 1:
                        x = np.arange(len(last_7))
                        y = last_7.values
                        slope = float(np.polyfit(x, y, 1)[0])
                        state.study_hours_trend_7d = slope

            last_14 = obs_up_to_t.tail(14)['study_hours'].dropna()
            if len(last_14) > 0:
                state.avg_study_hours_14d = float(last_14.mean())

        # Session duration is only valid when session counts exist.
        if 'study_hours' in obs_up_to_t.columns and 'study_sessions' in obs_up_to_t.columns:
            last_7 = obs_up_to_t.tail(7)
            study_sum = last_7['study_hours'].dropna().sum()
            session_sum = last_7['study_sessions'].dropna().sum()
            if study_sum > 0 and session_sum > 0:
                state.avg_session_duration_7d = float(study_sum / session_sum)

        return state

    def _compute_recovery(self, obs_up_to_t: pd.DataFrame) -> RecoveryState:
        """Compute recovery state from sleep and stress data."""
        state = RecoveryState(recovery_baseline_hours=self.baseline_sleep)

        if 'sleep_hours' in obs_up_to_t.columns:
            last_7 = obs_up_to_t.tail(7)['sleep_hours'].dropna()
            if len(last_7) > 0:
                state.avg_sleep_hours_7d = float(last_7.mean())

                # Sleep variability
                if len(last_7) > 1:
                    state.sleep_variability_7d = float(last_7.std())

                # Sleep deficit
                deficit = (self.baseline_sleep - last_7).clip(lower=0).sum()
                state.sleep_deficit_7d_hours = float(deficit)
                state.sleep_debt_severity = float(min(1.0, deficit / 14.0))

            # Last 14 days
            last_14 = obs_up_to_t.tail(14)['sleep_hours'].dropna()
            if len(last_14) > 0:
                state.avg_sleep_hours_14d = float(last_14.mean())

        if 'recovery_index' in obs_up_to_t.columns:
            last_7_recovery = obs_up_to_t.tail(7)['recovery_index'].dropna()
            if len(last_7_recovery) > 0:
                state.recovery_score_7d = float(np.clip(last_7_recovery.mean(), 0.0, 1.0))

        # Rest days (study_hours < 0.5)
        if 'study_hours' in obs_up_to_t.columns:
            last_7 = obs_up_to_t.tail(7)
            rest_days = (last_7['study_hours'] < 0.5).sum()
            state.rest_days_7d = int(rest_days)

        # Recovery ratio
        if 'study_hours' in obs_up_to_t.columns and 'sleep_hours' in obs_up_to_t.columns:
            last_7 = obs_up_to_t.tail(7)
            study_sum = last_7['study_hours'].sum()
            sleep_sum = last_7['sleep_hours'].sum()
            if study_sum > 0:
                state.recovery_ratio_7d = float(sleep_sum / (study_sum + 0.1))

        if state.recovery_score_7d is None and state.avg_sleep_hours_7d is not None:
            sleep_adequacy = min(1.0, state.avg_sleep_hours_7d / self.baseline_sleep)
            debt_component = 1.0 - (state.sleep_debt_severity or 0.0)
            state.recovery_score_7d = float(np.clip((sleep_adequacy + debt_component) / 2.0, 0.0, 1.0))

        return state

    def _compute_workload(self, obs_up_to_t: pd.DataFrame, today_obs: pd.Series) -> WorkloadState:
        """Compute workload state from deadline and assignment data."""
        state = WorkloadState()

        # Current pending count
        if 'pending_assignments' in today_obs:
            state.pending_assignment_count = int(today_obs['pending_assignments'])
        if 'upcoming_deadlines_7d' in today_obs and pd.notna(today_obs['upcoming_deadlines_7d']):
            state.deadline_density_next_7_known = int(today_obs['upcoming_deadlines_7d'])

        # Upcoming deadlines trend
        if 'upcoming_deadlines_7d' in obs_up_to_t.columns:
            last_7 = obs_up_to_t.tail(7)['upcoming_deadlines_7d'].dropna()
            if len(last_7) > 1:
                x = np.arange(len(last_7))
                y = last_7.values
                slope = float(np.polyfit(x, y, 1)[0])
                state.deadline_density_trend_7d = slope

        # Workload pressure
        if 'workload_pressure' in obs_up_to_t.columns:
            last_7 = obs_up_to_t.tail(7)['workload_pressure'].dropna()
            if len(last_7) > 0:
                state.workload_pressure_score_7d = float(last_7.mean())

        if {'assignment_due_today', 'missed_deadline_observed'}.issubset(obs_up_to_t.columns):
            last_14 = obs_up_to_t.tail(14)
            due_count = int(last_14['assignment_due_today'].fillna(0).sum())
            if due_count > 0:
                missed_count = int(last_14['missed_deadline_observed'].fillna(0).sum())
                submitted_rate = max(0.0, min(1.0, (due_count - missed_count) / due_count))
                state.submission_rate_14d = float(submitted_rate)
                state.submissions_on_time_pct_14d = float(submitted_rate)

        return state

    def _compute_engagement(self, obs_up_to_t: pd.DataFrame) -> EngagementState:
        """Compute engagement state from platform and stress data."""
        state = EngagementState()

        if 'platform_interactions' in obs_up_to_t.columns:
            last_7 = obs_up_to_t.tail(7)['platform_interactions'].dropna()
            if len(last_7) > 0:
                state.platform_interactions_7d_avg = float(last_7.mean())
            if len(last_7) > 1:
                state.interaction_trend_7d = self._ols_slope(last_7.values)

        if 'engagement_score' in obs_up_to_t.columns:
            last_7_engagement = obs_up_to_t.tail(7)['engagement_score'].dropna()
            if len(last_7_engagement) > 0:
                engagement_mean = float(np.clip(last_7_engagement.mean(), 0.0, 1.0))
                state.interaction_engagement_score = engagement_mean
                state.engagement_composite_score = engagement_mean

        if 'stress_level' in obs_up_to_t.columns:
            last_7 = obs_up_to_t.tail(7)['stress_level'].dropna()
            if len(last_7) > 0:
                # Stress is on [0.1, 1.0] in simulator; map to [1, 5] Likert
                stress_mean = float(last_7.mean())
                state.avg_stress_7d = 1.0 + 4.0 * stress_mean  # [1, 5]

                if len(last_7) > 1:
                    x = np.arange(len(last_7))
                    y = last_7.values
                    slope = float(np.polyfit(x, y, 1)[0])
                    state.stress_trend_7d = slope

        return state

    def _compute_temporal(self, day: int) -> TemporalContext:
        """Compute temporal context."""
        state = TemporalContext()
        state.day_of_semester = day
        state.week_of_semester = (day - 1) // 7 + 1
        state.day_of_week = (day - 1) % 7

        # Determine semester phase
        if day < 29:
            state.semester_phase = "early"
        elif day < 57:
            state.semester_phase = "mid"
        elif day < 85:
            state.semester_phase = "late"
        else:
            state.semester_phase = "exam"

        state.is_midterm_period = 29 <= day <= 49
        state.is_exam_period = day >= 85
        state.days_until_exam_period = max(0, 85 - day)

        return state

    def _compute_academic_load_score(
        self,
        obs_up_to_t: pd.DataFrame,
        workload: WorkloadState,
    ) -> Optional[float]:
        """
        Equal-weight normalized academic load from current known load proxies.

        Inputs are bounded to [0, 1]: 7-day workload pressure, current pending
        assignments/10, and current known deadline density/7. Equal weighting is
        used because no learned or validated domain weights exist here.
        """
        components = []
        required_sources = {
            "workload_pressure",
            "pending_assignments",
            "upcoming_deadlines_7d",
        }
        if not required_sources.issubset(obs_up_to_t.columns):
            return None
        if workload.workload_pressure_score_7d is None or workload.deadline_density_next_7_known is None:
            return None
        components.append(float(np.clip(workload.workload_pressure_score_7d, 0.0, 1.0)))
        components.append(float(np.clip(workload.pending_assignment_count / 10.0, 0.0, 1.0)))
        components.append(float(np.clip(workload.deadline_density_next_7_known / 7.0, 0.0, 1.0)))
        return float(np.mean(components))

    @staticmethod
    def _ols_slope(values) -> float:
        x = np.arange(len(values))
        return float(np.polyfit(x, values, 1)[0])

    @staticmethod
    def _has_column_values(df: pd.DataFrame, col: str) -> bool:
        return col in df.columns and df[col].dropna().shape[0] > 0

    def _validate_internal_stress(self, obs_up_to_t: pd.DataFrame) -> None:
        """TwinEngine expects internal stress_level values on [0, 1]."""
        if 'stress_level' not in obs_up_to_t.columns:
            return
        stress = pd.to_numeric(obs_up_to_t['stress_level'], errors='coerce').dropna()
        if len(stress) == 0:
            return
        if not np.isfinite(stress).all() or (stress < 0).any() or (stress > 1).any():
            raise ValueError("TwinEngine expects internal stress_level values in [0, 1]")

    def _build_provenance(
        self,
        state: StudentTwinState,
        obs_up_to_t: pd.DataFrame,
        today_obs: pd.Series,
    ) -> dict:
        """Build compact field provenance without changing existing value shapes."""
        prov = {}

        def add(path, ptype, source, window=None, unit=None, formula_id=None, imputed=False):
            prov[path] = FieldProvenance(
                type=ptype,
                source=source,
                window=window,
                unit=unit,
                formula_id=formula_id,
                imputed=imputed,
            )

        for col in today_obs.index:
            add(f"raw_latest.{col}", "observed", col, "current_day")

        derived_specs = {
            "academic.attendance_rate_7d": ("attendance_rate", "7d", "rate", "MEAN_7D"),
            "academic.attendance_trend_7d": ("attendance_rate", "7d", "rate/day", "OLS_SLOPE_7D"),
            "academic.attendance_rate_30d": ("attendance_rate", "30d", "rate", "MEAN_30D"),
            "academic.recent_grades_mean": ("grade", "last_5_observed", "0..1", "MEAN_LAST5_NORMALIZED"),
            "academic.grade_trend_30d": ("grade", "last_5_observed", "grade_fraction/day", "OLS_SLOPE_LAST5"),
            "academic.grades_below_personal_mean_pct": ("grade", "prior_history_vs_recent5", "rate", "RECENT_BELOW_PRIOR_MEAN"),
            "academic.missed_deadlines_14d": ("missed_deadline_observed", "14d", "count", "SUM_14D"),
            "academic.academic_load_score": ("workload_pressure,pending_assignments,upcoming_deadlines_7d", "current/7d", "0..1", "EQUAL_WEIGHT_LOAD_PROXY"),
            "behavioral.avg_study_hours_3d": ("study_hours", "3d", "hours/day", "MEAN_3D"),
            "behavioral.avg_study_hours_7d": ("study_hours", "7d", "hours/day", "MEAN_7D"),
            "behavioral.avg_study_hours_14d": ("study_hours", "14d", "hours/day", "MEAN_14D"),
            "behavioral.study_hours_trend_7d": ("study_hours", "7d", "hours/day/day", "OLS_SLOPE_7D"),
            "behavioral.study_variability_7d": ("study_hours", "7d", "coefficient", "STD_OVER_MEAN_7D"),
            "behavioral.study_consistency_score": ("study_hours", "7d", "0..1", "ONE_MINUS_HALF_VARIABILITY"),
            "behavioral.avg_session_duration_7d": ("study_hours,study_sessions", "7d", "hours/session", "STUDY_HOURS_PER_SESSION"),
            "recovery.avg_sleep_hours_7d": ("sleep_hours", "7d", "hours/night", "MEAN_7D"),
            "recovery.avg_sleep_hours_14d": ("sleep_hours", "14d", "hours/night", "MEAN_14D"),
            "recovery.sleep_variability_7d": ("sleep_hours", "7d", "hours", "STD_7D"),
            "recovery.sleep_deficit_7d_hours": ("sleep_hours", "7d", "hours", "BASELINE_MINUS_SLEEP_SUM"),
            "recovery.sleep_debt_severity": ("sleep_hours", "7d", "0..1", "SLEEP_DEFICIT_OVER_14"),
            "recovery.rest_days_7d": ("study_hours", "7d", "count", "COUNT_STUDY_LT_0_5"),
            "recovery.recovery_ratio_7d": ("sleep_hours,study_hours", "7d", "ratio", "SLEEP_SUM_OVER_STUDY_SUM"),
            "recovery.recovery_score_7d": ("recovery_index or sleep_hours", "7d", "0..1", "RECOVERY_INDEX_MEAN_OR_SLEEP_ADEQUACY"),
            "workload.pending_assignment_count": ("pending_assignments", "current_day", "count", "CURRENT_VALUE"),
            "workload.deadline_density_next_7_known": ("upcoming_deadlines_7d", "known_next_7d", "count", "CURRENT_KNOWN_SCHEDULE"),
            "workload.deadline_density_trend_7d": ("upcoming_deadlines_7d", "7d", "count/day", "OLS_SLOPE_7D"),
            "workload.workload_pressure_score_7d": ("workload_pressure", "7d", "0..1", "MEAN_7D"),
            "workload.submission_rate_14d": ("assignment_due_today,missed_deadline_observed", "14d", "rate", "SUBMITTED_DUE_RATIO"),
            "workload.submissions_on_time_pct_14d": ("assignment_due_today,missed_deadline_observed", "14d", "rate", "SUBMITTED_DUE_RATIO"),
            "engagement.platform_interactions_7d_avg": ("platform_interactions", "7d", "count/day", "MEAN_7D"),
            "engagement.interaction_trend_7d": ("platform_interactions", "7d", "count/day", "OLS_SLOPE_7D"),
            "engagement.interaction_engagement_score": ("engagement_score", "7d", "0..1", "MEAN_7D"),
            "engagement.avg_stress_7d": ("stress_level", "7d", "1..5 Likert", "ONE_PLUS_FOUR_TIMES_INTERNAL_STRESS"),
            "engagement.stress_trend_7d": ("stress_level", "7d", "internal_stress/day", "OLS_SLOPE_7D"),
            "engagement.engagement_composite_score": ("engagement_score", "7d", "0..1", "MEAN_7D"),
        }

        for path, (source, window, unit, formula_id) in derived_specs.items():
            layer_name, field_name = path.split(".", 1)
            value = getattr(getattr(state, layer_name), field_name)
            if value is None or not self._source_available(obs_up_to_t, source):
                add(path, "imputed_default", "unavailable_from_current_observations", window, unit, "UNAVAILABLE", True)
            else:
                add(path, "derived", source, window, unit, formula_id)

        unavailable_defaults = {
            "academic.active_subjects_count": ("subject_id/course_id", "count", "UNAVAILABLE_NO_SUBJECT_DATA"),
            "behavioral.break_rate_7d": ("break_events", "breaks/hour", "UNAVAILABLE_NO_BREAK_DATA"),
            "behavioral.distraction_rate_7d": ("distraction_events", "count/session", "UNAVAILABLE_NO_DISTRACTION_DATA"),
            "behavioral.focus_quality_7d_avg": ("focus_quality", "1..5 Likert", "UNAVAILABLE_NO_FOCUS_DATA"),
            "behavioral.procrastination_index_7d": ("submission_timing", "0..1", "UNAVAILABLE_NO_SUBMISSION_TIMING"),
            "workload.pending_assignment_effort_hours": ("assignment_effort_hours", "hours", "UNAVAILABLE_NO_EFFORT_DATA"),
            "workload.effort_study_gap_7d": ("assignment_effort_hours,study_hours", "hours/week", "UNAVAILABLE_NO_EFFORT_DATA"),
            "engagement.avg_confidence_7d": ("confidence", "1..5 Likert", "UNAVAILABLE_NO_CONFIDENCE_DATA"),
            "engagement.avg_wellbeing_7d": ("wellbeing", "1..5 Likert", "UNAVAILABLE_NO_WELLBEING_DATA"),
        }
        for path, (source, unit, formula_id) in unavailable_defaults.items():
            layer_name, field_name = path.split(".", 1)
            value = getattr(getattr(state, layer_name), field_name)
            if path == "academic.active_subjects_count" and value > 0:
                add(path, "derived", source, "30d", unit, "ACTIVE_SUBJECT_NUNIQUE")
            else:
                add(path, "imputed_default", source, None, unit, formula_id, True)

        temporal_fields = [
            "day_of_semester", "week_of_semester", "day_of_week",
            "is_exam_period", "is_midterm_period", "semester_phase",
            "days_until_exam_period",
        ]
        for field in temporal_fields:
            add(f"temporal.{field}", "derived", "day", "current_day", None, "SEMESTER_CALENDAR_RULE")

        prediction_fields = [
            "overload_risk_probability", "overload_label_binary", "strain_index",
            "feature_importances", "model_confidence",
        ]
        for field in prediction_fields:
            add(f"predictions.{field}", "predicted", "PredictionService", "current_state", None, "MODEL_OUTPUT")

        history_fields = ["total_observations", "observations_with_full_data"]
        for field in history_fields:
            add(f"history.{field}", "derived", "observations", "1_to_current_day", "count", "HISTORY_COUNT")

        return prov

    @staticmethod
    def _source_available(df: pd.DataFrame, source: str) -> bool:
        if source == "day":
            return True
        if " or " in source:
            return any(
                part.strip() in df.columns and df[part.strip()].dropna().shape[0] > 0
                for part in source.split(" or ")
            )
        cols = [part.strip() for part in source.split(",")]
        return all(col in df.columns and df[col].dropna().shape[0] > 0 for col in cols)

    def _compute_history(self, obs_up_to_t: pd.DataFrame) -> HistorySummary:
        """Compute historical summary."""
        state = HistorySummary()
        state.total_observations = len(obs_up_to_t)

        # Count observations with reasonably complete data
        numeric_cols = ['study_hours', 'sleep_hours', 'stress_level', 'grade']
        if len(obs_up_to_t) > 0:
            completeness = obs_up_to_t[numeric_cols].notna().mean(axis=1)
            state.observations_with_full_data = int((completeness >= 0.8).sum())

        return state
