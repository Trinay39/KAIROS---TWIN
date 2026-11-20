"""
KAIROS-TWIN Phase 6: Workload Agent.

Analyzes workload pressure and deadline density.
"""
from __future__ import annotations
from typing import List
from core.schemas import WorkloadState
from agents.base_agent import BaseAgent, AgentDiagnosis, Severity


class WorkloadAgent(BaseAgent):
    """
    Analyzes workload and deadline indicators.

    Monitors:
    - Pending assignment count
    - Deadline density
    - Workload pressure score
    - Submission rates
    - Effort-study gap

    Triggers scenarios:
    - REDUCE_WORKLOAD: When workload pressure is high
    - MOVE_ASSIGNMENT: When deadlines are clustered
    - REMOVE_ASSIGNMENT: When workload is unmanageable
    - REDUCE_DEADLINE_DENSITY: When deadline clustering is severe
    """

    def __init__(self):
        super().__init__(
            name="WorkloadAgent",
            description="Analyzes workload pressure and deadline density"
        )

    def diagnose(self, state_layer: WorkloadState, day: int = 0) -> List[AgentDiagnosis]:
        """
        Analyze workload state for problems.

        Args:
            state_layer: WorkloadState object
            day: Current semester day

        Returns:
            List of diagnoses (empty if no issues)
        """
        if state_layer is None:
            return []

        diagnoses = []

        # Check 1: High pending assignment count
        if state_layer.pending_assignment_count > 5:
            severity = self._classify_severity(
                float(state_layer.pending_assignment_count),
                {"low": 5.0, "medium": 8.0, "high": 12.0, "critical": 15.0}
            )
            diagnoses.append(self._build_diagnosis(
                issue_name="high_pending_assignments",
                severity=severity,
                description=f"{state_layer.pending_assignment_count} pending assignments",
                affected_fields=["pending_assignment_count", "pending_assignment_effort_hours"],
                suggested_scenario_types=["REDUCE_WORKLOAD", "MOVE_ASSIGNMENT"],
                confidence=0.92,
            ))

        # Check 2: High deadline density
        if state_layer.deadline_density_next_7_known is not None and state_layer.deadline_density_next_7_known > 3:
            severity = self._classify_severity(
                float(state_layer.deadline_density_next_7_known),
                {"low": 3.0, "medium": 5.0, "high": 7.0, "critical": 10.0}
            )
            diagnoses.append(self._build_diagnosis(
                issue_name="deadline_clustering",
                severity=severity,
                description=f"{state_layer.deadline_density_next_7_known} deadlines in next 7 days",
                affected_fields=["deadline_density_next_7_known", "deadline_density_trend_7d"],
                suggested_scenario_types=["MOVE_ASSIGNMENT", "REDUCE_DEADLINE_DENSITY"],
                confidence=0.88,
            ))

        # Check 3: High workload pressure
        if (
            state_layer.workload_pressure_score_7d is not None
            and state_layer.workload_pressure_score_7d > 0.6
        ):
            severity = self._classify_severity(
                state_layer.workload_pressure_score_7d,
                {"low": 0.60, "medium": 0.75, "high": 0.85, "critical": 0.95}
            )
            diagnoses.append(self._build_diagnosis(
                issue_name="high_workload_pressure",
                severity=severity,
                description=f"Workload pressure score is {state_layer.workload_pressure_score_7d:.2f}",
                affected_fields=["workload_pressure_score_7d", "pending_assignment_count"],
                suggested_scenario_types=["REDUCE_WORKLOAD", "REMOVE_ASSIGNMENT"],
                confidence=0.90,
            ))

        # Check 4: Rising deadline density trend
        if state_layer.deadline_density_trend_7d is not None and state_layer.deadline_density_trend_7d > 0.1:
            severity = self._classify_severity(
                state_layer.deadline_density_trend_7d,
                {"low": 0.10, "medium": 0.20, "high": 0.35, "critical": 0.50}
            )
            diagnoses.append(self._build_diagnosis(
                issue_name="rising_deadline_density",
                severity=severity,
                description=f"Deadline density increasing at {state_layer.deadline_density_trend_7d:.3f} per day",
                affected_fields=["deadline_density_trend_7d"],
                suggested_scenario_types=["MOVE_ASSIGNMENT", "REDUCE_DEADLINE_DENSITY"],
                confidence=0.82,
            ))

        # Check 5: Low submission rate
        if state_layer.submission_rate_14d is not None and state_layer.submission_rate_14d < 0.8:
            severity = self._classify_severity(
                1.0 - state_layer.submission_rate_14d,
                {"low": 0.10, "medium": 0.25, "high": 0.40, "critical": 0.60}
            )
            diagnoses.append(self._build_diagnosis(
                issue_name="low_submission_rate",
                severity=severity,
                description=f"Submission rate (14d) is {state_layer.submission_rate_14d:.1%}",
                affected_fields=["submission_rate_14d", "submissions_on_time_pct_14d"],
                suggested_scenario_types=["REDUCE_WORKLOAD"],
                confidence=0.85,
            ))

        # Check 6: Effort-study gap (effort exceeds study time)
        if state_layer.effort_study_gap_7d is not None and state_layer.effort_study_gap_7d > 2.0:
            severity = self._classify_severity(
                state_layer.effort_study_gap_7d,
                {"low": 2.0, "medium": 4.0, "high": 6.0, "critical": 8.0}
            )
            diagnoses.append(self._build_diagnosis(
                issue_name="effort_study_mismatch",
                severity=severity,
                description=f"Effort exceeds study time by {state_layer.effort_study_gap_7d:.1f}h/week",
                affected_fields=["effort_study_gap_7d"],
                suggested_scenario_types=["INCREASE_STUDY_TIME", "REDUCE_WORKLOAD"],
                confidence=0.80,
            ))

        return diagnoses

    def get_supported_scenarios(self) -> List[str]:
        """Return scenario types this agent can trigger."""
        return ["REDUCE_WORKLOAD", "MOVE_ASSIGNMENT", "REMOVE_ASSIGNMENT", "REDUCE_DEADLINE_DENSITY", "INCREASE_STUDY_TIME"]
