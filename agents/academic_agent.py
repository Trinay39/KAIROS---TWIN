"""
KAIROS-TWIN Phase 6: Academic Agent.

Analyzes academic performance and deadline compliance.
"""
from __future__ import annotations
from typing import List
from core.schemas import AcademicState
from agents.base_agent import BaseAgent, AgentDiagnosis, Severity


class AcademicAgent(BaseAgent):
    """
    Analyzes academic performance indicators.

    Monitors:
    - Attendance rate and trends
    - Grade performance and deterioration
    - Missed deadlines
    - Academic load score

    Triggers scenarios:
    - REDUCE_WORKLOAD: When academic load is high
    - MOVE_ASSIGNMENT: When deadline clustering is detected
    - REMOVE_ASSIGNMENT: When load is unmanageable
    """

    def __init__(self):
        super().__init__(
            name="AcademicAgent",
            description="Analyzes academic performance and deadline compliance"
        )

    def diagnose(self, state_layer: AcademicState, day: int = 0) -> List[AgentDiagnosis]:
        """
        Analyze academic state for problems.

        Args:
            state_layer: AcademicState object
            day: Current semester day

        Returns:
            List of diagnoses (empty if no issues)
        """
        if state_layer is None:
            return []

        diagnoses = []

        # Check 1: Grade deterioration
        if state_layer.grade_trend_30d is not None and state_layer.grade_trend_30d < -0.01:
            severity = self._classify_severity(
                abs(state_layer.grade_trend_30d),
                {"low": 0.01, "medium": 0.03, "high": 0.05, "critical": 0.08}
            )
            diagnoses.append(self._build_diagnosis(
                issue_name="grade_deterioration",
                severity=severity,
                description=f"Grades declining at {state_layer.grade_trend_30d:.3f} per day over 30 days",
                affected_fields=["grade_trend_30d", "recent_grades_mean"],
                suggested_scenario_types=["REDUCE_WORKLOAD"],
                confidence=0.85,
            ))

        # Check 2: Low attendance
        if state_layer.attendance_rate_7d is not None and state_layer.attendance_rate_7d < 0.85:
            severity = self._classify_severity(
                1.0 - state_layer.attendance_rate_7d,
                {"low": 0.10, "medium": 0.20, "high": 0.35, "critical": 0.50}
            )
            diagnoses.append(self._build_diagnosis(
                issue_name="low_attendance",
                severity=severity,
                description=f"7-day attendance rate is {state_layer.attendance_rate_7d:.1%}",
                affected_fields=["attendance_rate_7d", "attendance_trend_7d"],
                suggested_scenario_types=["REDUCE_WORKLOAD"],
                confidence=0.90,
            ))

        # Check 3: Missed deadlines
        if state_layer.missed_deadlines_14d > 0:
            severity = self._classify_severity(
                float(state_layer.missed_deadlines_14d),
                {"low": 1.0, "medium": 2.0, "high": 4.0, "critical": 6.0}
            )
            diagnoses.append(self._build_diagnosis(
                issue_name="missed_deadlines",
                severity=severity,
                description=f"{state_layer.missed_deadlines_14d} deadlines missed in past 14 days",
                affected_fields=["missed_deadlines_14d"],
                suggested_scenario_types=["MOVE_ASSIGNMENT", "REDUCE_WORKLOAD"],
                confidence=0.95,
            ))

        # Check 4: High academic load
        if state_layer.academic_load_score is not None and state_layer.academic_load_score > 0.7:
            severity = self._classify_severity(
                state_layer.academic_load_score,
                {"low": 0.7, "medium": 0.8, "high": 0.9, "critical": 0.95}
            )
            diagnoses.append(self._build_diagnosis(
                issue_name="high_academic_load",
                severity=severity,
                description=f"Academic load score is {state_layer.academic_load_score:.2f}",
                affected_fields=["academic_load_score", "active_subjects_count"],
                suggested_scenario_types=["REDUCE_WORKLOAD", "REMOVE_ASSIGNMENT"],
                confidence=0.88,
            ))

        # Check 5: Grades below personal mean
        if state_layer.grades_below_personal_mean_pct is not None and state_layer.grades_below_personal_mean_pct > 0.3:
            severity = self._classify_severity(
                state_layer.grades_below_personal_mean_pct,
                {"low": 0.30, "medium": 0.50, "high": 0.70, "critical": 0.85}
            )
            diagnoses.append(self._build_diagnosis(
                issue_name="underperforming_grades",
                severity=severity,
                description=f"{state_layer.grades_below_personal_mean_pct:.1%} of grades below personal mean",
                affected_fields=["grades_below_personal_mean_pct", "recent_grades_mean"],
                suggested_scenario_types=["REDUCE_WORKLOAD", "INCREASE_STUDY_TIME"],
                confidence=0.82,
            ))

        return diagnoses

    def get_supported_scenarios(self) -> List[str]:
        """Return scenario types this agent can trigger."""
        return ["REDUCE_WORKLOAD", "MOVE_ASSIGNMENT", "REMOVE_ASSIGNMENT", "INCREASE_STUDY_TIME"]
