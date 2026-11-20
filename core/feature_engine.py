"""
KAIROS-TWIN Phase 3: Feature Engineering.

Extracts 46 ML-ready features from StudentTwinState(t).

All features are classified as CURRENT or PAST-DERIVED.
No feature contains information from [t+1, t+7] (leakage prevention).

Feature list (46 total):
- Academic (7): attendance, grades, subject count, missed deadlines
- Behavioral (9): study hours, variability, consistency, session depth, procrastination
- Recovery (8): sleep, variability, deficit, rest days, recovery ratio
- Workload (7): pending count, effort, deadline trend, pressure, submission rate
- Engagement (5): platform interactions, stress, confidence, wellbeing
- Temporal (6): week, day, exam period, midterm, days until exam
- Interaction (4): workload-recovery imbalance, etc.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from core.schemas import StudentTwinState


class FeatureEngine:
    """Extracts ML-ready features from StudentTwinState."""

    # Feature list (in order)
    FEATURE_NAMES = [
        # Academic (7)
        'attendance_rate_7d',
        'attendance_trend_7d',
        'recent_grades_mean',
        'grade_trend_30d',
        'grades_below_personal_mean_pct',
        'active_subjects_count',
        'missed_deadlines_14d',

        # Behavioral (9)
        'avg_study_hours_3d',
        'avg_study_hours_7d',
        'study_variability_7d',
        'study_consistency_score',
        'avg_session_duration_7d',
        'break_rate_7d',
        'distraction_rate_7d',
        'focus_quality_7d_avg',
        'procrastination_index_7d',

        # Recovery (8)
        'avg_sleep_hours_7d',
        'sleep_variability_7d',
        'sleep_deficit_7d_hours',
        'sleep_debt_severity',
        'rest_days_7d',
        'recovery_ratio_7d',
        'recovery_score_7d',
        'recovery_deficit_score',

        # Workload (7)
        'pending_assignment_count',
        'pending_assignment_effort_hours',
        'deadline_density_trend_7d',
        'workload_pressure_score_7d',
        'submission_rate_14d',
        'submissions_on_time_pct_14d',
        'effort_study_gap_7d',

        # Engagement (5)
        'platform_interactions_7d_avg',
        'interaction_trend_7d',
        'interaction_engagement_score',
        'avg_stress_7d',
        'avg_confidence_7d',

        # Temporal (6)
        'week_of_semester',
        'day_of_week_sine',
        'day_of_week_cosine',
        'is_midterm_period',
        'is_exam_period',
        'days_until_exam_period',

        # Interaction (4)
        'workload_recovery_imbalance',
        'deadline_urgency_effort_ratio',
        'study_stress_coherence',
        'recovery_confidence_coupling',
    ]

    def __init__(self):
        """Initialize feature engine."""
        assert len(self.FEATURE_NAMES) == 46, f"Expected 46 features, got {len(self.FEATURE_NAMES)}"

    def extract_features(self, twin_state: StudentTwinState) -> Dict[str, float]:
        """
        Extract all 46 features from StudentTwinState.

        Args:
            twin_state: StudentTwinState at time t

        Returns:
            Dictionary {feature_name: value} with all 46 features
        """
        features = {}

        # Academic features (7)
        features['attendance_rate_7d'] = self._safe_get(
            twin_state.academic.attendance_rate_7d, 0.9, [0, 1]
        )
        features['attendance_trend_7d'] = self._safe_get(
            twin_state.academic.attendance_trend_7d, 0.0, [-0.2, 0.2]
        )
        features['recent_grades_mean'] = self._safe_get(
            twin_state.academic.recent_grades_mean, 0.65, [0, 1]
        )
        features['grade_trend_30d'] = self._safe_get(
            twin_state.academic.grade_trend_30d, 0.0, [-0.2, 0.2]
        )
        features['grades_below_personal_mean_pct'] = self._safe_get(
            twin_state.academic.grades_below_personal_mean_pct, 0.2, [0, 1]
        )
        # The live twin no longer invents a subject count. Preserve the legacy
        # training-time constant only inside the ML adapter to keep the frozen
        # 46-feature contract compatible with the existing artifact.
        active_subjects = (
            twin_state.academic.active_subjects_count
            if twin_state.academic.active_subjects_count > 0
            else 4
        )
        features['active_subjects_count'] = float(active_subjects)
        features['missed_deadlines_14d'] = float(twin_state.academic.missed_deadlines_14d)

        # Behavioral features (9)
        features['avg_study_hours_3d'] = self._safe_get(
            twin_state.behavioral.avg_study_hours_3d, 4.0, [0.1, 18]
        )
        features['avg_study_hours_7d'] = self._safe_get(
            twin_state.behavioral.avg_study_hours_7d, 3.7, [0.1, 18]
        )
        features['study_variability_7d'] = self._safe_get(
            twin_state.behavioral.study_variability_7d, 0.4, [0, 5]
        )
        features['study_consistency_score'] = self._safe_get(
            twin_state.behavioral.study_consistency_score, 0.8, [0, 1]
        )
        features['avg_session_duration_7d'] = self._safe_get(
            twin_state.behavioral.avg_session_duration_7d, 0.5, [0.1, 4]
        )
        features['break_rate_7d'] = self._safe_get(
            twin_state.behavioral.break_rate_7d, 0.05, [0, 2]
        )
        features['distraction_rate_7d'] = self._safe_get(
            twin_state.behavioral.distraction_rate_7d, 0.1, [0, 5]
        )
        features['focus_quality_7d_avg'] = self._safe_get(
            twin_state.behavioral.focus_quality_7d_avg, 3.0, [1, 5]
        )
        features['procrastination_index_7d'] = self._safe_get(
            twin_state.behavioral.procrastination_index_7d, 0.3, [0, 1]
        )

        # Recovery features (8)
        features['avg_sleep_hours_7d'] = self._safe_get(
            twin_state.recovery.avg_sleep_hours_7d, 7.1, [3, 12]
        )
        features['sleep_variability_7d'] = self._safe_get(
            twin_state.recovery.sleep_variability_7d, 0.2, [0, 3]
        )
        features['sleep_deficit_7d_hours'] = self._safe_get(
            twin_state.recovery.sleep_deficit_7d_hours, 2.0, [0, 49]
        )
        features['sleep_debt_severity'] = self._safe_get(
            twin_state.recovery.sleep_debt_severity, 0.1, [0, 1]
        )
        features['rest_days_7d'] = float(twin_state.recovery.rest_days_7d)
        features['recovery_ratio_7d'] = self._safe_get(
            twin_state.recovery.recovery_ratio_7d, 2.0, [0, 10]
        )
        features['recovery_score_7d'] = self._safe_get(
            twin_state.recovery.recovery_score_7d, 0.8, [0, 1]
        )

        # Additional recovery feature: deficit score
        sleep_deficit = self._safe_get(twin_state.recovery.sleep_deficit_7d_hours, 2.0, [0, 49])
        features['recovery_deficit_score'] = min(1.0, sleep_deficit / 14.0)

        # Workload features (7)
        features['pending_assignment_count'] = float(twin_state.workload.pending_assignment_count)
        features['pending_assignment_effort_hours'] = self._safe_get(
            twin_state.workload.pending_assignment_effort_hours, 10.0, [0, 150]
        )
        features['deadline_density_trend_7d'] = self._safe_get(
            twin_state.workload.deadline_density_trend_7d, 0.0, [-5, 5]
        )
        features['workload_pressure_score_7d'] = self._safe_get(
            twin_state.workload.workload_pressure_score_7d, 0.3, [0, 1]
        )
        features['submission_rate_14d'] = self._safe_get(
            twin_state.workload.submission_rate_14d, 0.9, [0, 1]
        )
        features['submissions_on_time_pct_14d'] = self._safe_get(
            twin_state.workload.submissions_on_time_pct_14d, 0.85, [0, 1]
        )
        features['effort_study_gap_7d'] = self._safe_get(
            twin_state.workload.effort_study_gap_7d, 0.0, [-10, 10]
        )

        # Engagement features (5)
        features['platform_interactions_7d_avg'] = self._safe_get(
            twin_state.engagement.platform_interactions_7d_avg, 15.9, [0, 200]
        )
        features['interaction_trend_7d'] = self._safe_get(
            twin_state.engagement.interaction_trend_7d, 0.0, [-50, 50]
        )
        features['interaction_engagement_score'] = self._safe_get(
            twin_state.engagement.interaction_engagement_score, 0.6, [0, 1]
        )
        features['avg_stress_7d'] = self._safe_get(
            twin_state.engagement.avg_stress_7d, 2.8, [1, 5]
        )
        features['avg_confidence_7d'] = self._safe_get(
            twin_state.engagement.avg_confidence_7d, 3.0, [1, 5]
        )

        # Temporal features (6)
        features['week_of_semester'] = float(twin_state.temporal.week_of_semester)
        # Cyclic encoding for day of week
        dow = twin_state.temporal.day_of_week
        features['day_of_week_sine'] = np.sin(2 * np.pi * dow / 7.0)
        features['day_of_week_cosine'] = np.cos(2 * np.pi * dow / 7.0)
        features['is_midterm_period'] = float(twin_state.temporal.is_midterm_period)
        features['is_exam_period'] = float(twin_state.temporal.is_exam_period)
        features['days_until_exam_period'] = float(twin_state.temporal.days_until_exam_period)

        # Interaction features (4)
        study_7d = self._safe_get(twin_state.behavioral.avg_study_hours_7d, 3.7, [0.1, 18])
        workload = self._safe_get(twin_state.workload.workload_pressure_score_7d, 0.3, [0, 1])
        recovery_ratio = self._safe_get(twin_state.recovery.recovery_ratio_7d, 2.0, [0, 10])
        stress_7d = self._safe_get(twin_state.engagement.avg_stress_7d, 2.8, [1, 5])

        features['workload_recovery_imbalance'] = (workload * 100) / (recovery_ratio + 0.1) - 50
        features['deadline_urgency_effort_ratio'] = (
            features['deadline_density_trend_7d'] / (study_7d + 0.1)
            if features['deadline_density_trend_7d'] != 0 else 0.0
        )

        # Study-stress coherence: negative correlation expected (high stress → low study)
        if len(self.FEATURE_NAMES) >= 44:
            features['study_stress_coherence'] = -0.5 * (stress_7d - 3.0) / 2.0  # simplified

        # Recovery-confidence coupling
        if len(self.FEATURE_NAMES) >= 46:
            recovery_score = self._safe_get(twin_state.recovery.recovery_score_7d, 0.8, [0, 1])
            confidence = self._safe_get(twin_state.engagement.avg_confidence_7d, 3.0, [1, 5])
            features['recovery_confidence_coupling'] = (recovery_score - 0.5) * (confidence - 3.0) / 5.0

        # Verify all features are present
        missing = set(self.FEATURE_NAMES) - set(features.keys())
        if missing:
            raise KeyError(f"Missing features: {missing}")

        return features

    def extract_features_df(self, twin_states: List[StudentTwinState]) -> pd.DataFrame:
        """
        Extract features from a list of StudentTwinStates.

        Args:
            twin_states: List of StudentTwinState objects

        Returns:
            DataFrame with rows = states, columns = features
        """
        rows = []
        for state in twin_states:
            features = self.extract_features(state)
            row = {'student_id': state.student_id, 'day': state.day}
            row.update(features)
            rows.append(row)

        return pd.DataFrame(rows)

    @staticmethod
    def _safe_get(value, default, valid_range):
        """
        Safely retrieve a value with fallback and clipping.

        Args:
            value: The value to retrieve (may be None)
            default: Default value if None
            valid_range: [min, max] to clip to

        Returns:
            Float value clipped to valid_range
        """
        if value is None:
            v = default
        else:
            v = float(value)

        return float(np.clip(v, valid_range[0], valid_range[1]))
