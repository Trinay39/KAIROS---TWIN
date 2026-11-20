"""
KAIROS-TWIN Phase 6: Behavioral Agent.

Analyzes study patterns, procrastination, and consistency.
"""
from __future__ import annotations
from typing import List
from core.schemas import BehavioralState
from agents.base_agent import BaseAgent, AgentDiagnosis, Severity


class BehavioralAgent(BaseAgent):
    """
    Analyzes behavioral and study patterns.

    Monitors:
    - Study hours and trends
    - Study consistency
    - Procrastination index
    - Focus quality
    - Distraction rate

    Triggers scenarios:
    - INCREASE_STUDY_TIME: When study hours are low
    - REDUCE_WORKLOAD: When study patterns are unsustainable
    """

    def __init__(self):
        super().__init__(
            name="BehavioralAgent",
            description="Analyzes study patterns and behavioral consistency"
        )

    def diagnose(self, state_layer: BehavioralState, day: int = 0) -> List[AgentDiagnosis]:
        """
        Analyze behavioral state for problems.

        Args:
            state_layer: BehavioralState object
            day: Current semester day

        Returns:
            List of diagnoses (empty if no issues)
        """
        if state_layer is None:
            return []

        diagnoses = []

        # Check 1: Low study hours
        if state_layer.avg_study_hours_7d is not None and state_layer.avg_study_hours_7d < 3.0:
            severity = self._classify_severity(
                5.0 - state_layer.avg_study_hours_7d,  # Higher gap = more severe
                {"low": 1.0, "medium": 2.0, "high": 3.0, "critical": 4.5}
            )
            diagnoses.append(self._build_diagnosis(
                issue_name="low_study_hours",
                severity=severity,
                description=f"Average study hours (7d) is {state_layer.avg_study_hours_7d:.1f}h/day, below recommended minimum",
                affected_fields=["avg_study_hours_7d", "avg_study_hours_3d"],
                suggested_scenario_types=["INCREASE_STUDY_TIME"],
                confidence=0.90,
            ))

        # Check 2: Declining study trend
        if state_layer.study_hours_trend_7d is not None and state_layer.study_hours_trend_7d < -0.3:
            severity = self._classify_severity(
                abs(state_layer.study_hours_trend_7d),
                {"low": 0.3, "medium": 0.6, "high": 1.0, "critical": 1.5}
            )
            diagnoses.append(self._build_diagnosis(
                issue_name="declining_study_trend",
                severity=severity,
                description=f"Study hours declining at {state_layer.study_hours_trend_7d:.2f}h/day per day",
                affected_fields=["study_hours_trend_7d", "avg_study_hours_7d"],
                suggested_scenario_types=["INCREASE_STUDY_TIME", "REDUCE_WORKLOAD"],
                confidence=0.85,
            ))

        # Check 3: Low study consistency
        if state_layer.study_consistency_score is not None and state_layer.study_consistency_score < 0.5:
            severity = self._classify_severity(
                1.0 - state_layer.study_consistency_score,
                {"low": 0.40, "medium": 0.55, "high": 0.70, "critical": 0.85}
            )
            diagnoses.append(self._build_diagnosis(
                issue_name="low_study_consistency",
                severity=severity,
                description=f"Study consistency score is {state_layer.study_consistency_score:.2f}",
                affected_fields=["study_consistency_score", "study_variability_7d"],
                suggested_scenario_types=["INCREASE_STUDY_TIME"],
                confidence=0.80,
            ))

        # Check 4: High procrastination
        if state_layer.procrastination_index_7d is not None and state_layer.procrastination_index_7d > 0.5:
            severity = self._classify_severity(
                state_layer.procrastination_index_7d,
                {"low": 0.50, "medium": 0.65, "high": 0.80, "critical": 0.90}
            )
            diagnoses.append(self._build_diagnosis(
                issue_name="high_procrastination",
                severity=severity,
                description=f"Procrastination index is {state_layer.procrastination_index_7d:.2f}",
                affected_fields=["procrastination_index_7d"],
                suggested_scenario_types=["INCREASE_STUDY_TIME", "REDUCE_WORKLOAD"],
                confidence=0.88,
            ))

        # Check 5: Low focus quality
        if state_layer.focus_quality_7d_avg is not None and state_layer.focus_quality_7d_avg < 3.0:
            severity = self._classify_severity(
                5.0 - state_layer.focus_quality_7d_avg,  # Higher gap = more severe
                {"low": 1.5, "medium": 2.0, "high": 2.5, "critical": 3.5}
            )
            diagnoses.append(self._build_diagnosis(
                issue_name="low_focus_quality",
                severity=severity,
                description=f"Focus quality (7d avg) is {state_layer.focus_quality_7d_avg:.1f}/5.0",
                affected_fields=["focus_quality_7d_avg", "distraction_rate_7d"],
                suggested_scenario_types=["INCREASE_STUDY_TIME"],
                confidence=0.75,
            ))

        # Check 6: High distraction rate
        if state_layer.distraction_rate_7d is not None and state_layer.distraction_rate_7d > 2.0:
            severity = self._classify_severity(
                state_layer.distraction_rate_7d,
                {"low": 2.0, "medium": 4.0, "high": 6.0, "critical": 8.0}
            )
            diagnoses.append(self._build_diagnosis(
                issue_name="high_distraction",
                severity=severity,
                description=f"Distraction rate is {state_layer.distraction_rate_7d:.1f} per session",
                affected_fields=["distraction_rate_7d", "focus_quality_7d_avg"],
                suggested_scenario_types=["INCREASE_STUDY_TIME"],
                confidence=0.78,
            ))

        return diagnoses

    def get_supported_scenarios(self) -> List[str]:
        """Return scenario types this agent can trigger."""
        return ["INCREASE_STUDY_TIME", "REDUCE_WORKLOAD"]
