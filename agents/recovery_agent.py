"""
KAIROS-TWIN Phase 6: Recovery Agent.

Analyzes sleep, stress, and recovery indicators.
"""
from __future__ import annotations
from typing import List
from core.schemas import RecoveryState, EngagementState
from agents.base_agent import BaseAgent, AgentDiagnosis, Severity


class RecoveryAgent(BaseAgent):
    """
    Analyzes recovery and wellbeing indicators.

    Monitors:
    - Sleep hours and deficit
    - Sleep variability
    - Recovery score
    - Stress levels (from EngagementState)
    - Confidence levels

    Triggers scenarios:
    - INCREASE_SLEEP: When sleep deficit is detected
    - REDUCE_WORKLOAD: When recovery is compromised
    """

    def __init__(self):
        super().__init__(
            name="RecoveryAgent",
            description="Analyzes sleep, stress, and recovery indicators"
        )

    def diagnose(
        self,
        state_layer,  # Can be RecoveryState or tuple of (RecoveryState, EngagementState)
        day: int = 0
    ) -> List[AgentDiagnosis]:
        """
        Analyze recovery state for problems.

        Args:
            state_layer: RecoveryState object, or tuple (RecoveryState, EngagementState)
            day: Current semester day

        Returns:
            List of diagnoses (empty if no issues)
        """
        # Handle both single state and tuple input
        if isinstance(state_layer, tuple):
            recovery_state, engagement_state = state_layer
        else:
            recovery_state = state_layer
            engagement_state = None

        if recovery_state is None:
            return []

        diagnoses = []

        # Check 1: Sleep deficit
        if recovery_state.sleep_deficit_7d_hours is not None and recovery_state.sleep_deficit_7d_hours > 5.0:
            severity = self._classify_severity(
                recovery_state.sleep_deficit_7d_hours,
                {"low": 5.0, "medium": 10.0, "high": 20.0, "critical": 30.0}
            )
            diagnoses.append(self._build_diagnosis(
                issue_name="sleep_deficit",
                severity=severity,
                description=f"Sleep deficit of {recovery_state.sleep_deficit_7d_hours:.1f} hours over 7 days",
                affected_fields=["sleep_deficit_7d_hours", "avg_sleep_hours_7d"],
                suggested_scenario_types=["INCREASE_SLEEP"],
                confidence=0.92,
            ))

        # Check 2: Low sleep hours
        if recovery_state.avg_sleep_hours_7d is not None and recovery_state.avg_sleep_hours_7d < 6.5:
            severity = self._classify_severity(
                8.0 - recovery_state.avg_sleep_hours_7d,  # Gap from 8h target
                {"low": 1.5, "medium": 2.5, "high": 3.5, "critical": 4.5}
            )
            diagnoses.append(self._build_diagnosis(
                issue_name="low_sleep",
                severity=severity,
                description=f"Average sleep is {recovery_state.avg_sleep_hours_7d:.1f}h/night, below recommended 7-9h",
                affected_fields=["avg_sleep_hours_7d", "sleep_deficit_7d_hours"],
                suggested_scenario_types=["INCREASE_SLEEP"],
                confidence=0.95,
            ))

        # Check 3: High sleep variability
        if recovery_state.sleep_variability_7d is not None and recovery_state.sleep_variability_7d > 1.5:
            severity = self._classify_severity(
                recovery_state.sleep_variability_7d,
                {"low": 1.5, "medium": 2.5, "high": 3.5, "critical": 4.5}
            )
            diagnoses.append(self._build_diagnosis(
                issue_name="irregular_sleep",
                severity=severity,
                description=f"Sleep variability is {recovery_state.sleep_variability_7d:.2f}h (std dev)",
                affected_fields=["sleep_variability_7d", "avg_sleep_hours_7d"],
                suggested_scenario_types=["INCREASE_SLEEP"],
                confidence=0.85,
            ))

        # Check 4: Low recovery score
        if recovery_state.recovery_score_7d is not None and recovery_state.recovery_score_7d < 0.5:
            severity = self._classify_severity(
                1.0 - recovery_state.recovery_score_7d,
                {"low": 0.40, "medium": 0.55, "high": 0.70, "critical": 0.85}
            )
            diagnoses.append(self._build_diagnosis(
                issue_name="low_recovery",
                severity=severity,
                description=f"Recovery score is {recovery_state.recovery_score_7d:.2f}",
                affected_fields=["recovery_score_7d", "rest_days_7d"],
                suggested_scenario_types=["INCREASE_SLEEP", "REDUCE_WORKLOAD"],
                confidence=0.88,
            ))

        # Check 5: High stress (from EngagementState if provided)
        if engagement_state is not None and engagement_state.avg_stress_7d is not None:
            # Stress is on [1, 5] scale or [0.1, 1.0] - detect which
            stress = engagement_state.avg_stress_7d
            if stress <= 1.0:
                # Already normalized [0.1, 1.0]
                stress_normalized = stress
            else:
                # [1, 5] scale - normalize to [0, 1]
                stress_normalized = (stress - 1.0) / 4.0

            if stress_normalized > 0.6:
                severity = self._classify_severity(
                    stress_normalized,
                    {"low": 0.60, "medium": 0.75, "high": 0.85, "critical": 0.95}
                )
                diagnoses.append(self._build_diagnosis(
                    issue_name="high_stress",
                    severity=severity,
                    description=f"Average stress level is {stress:.2f}",
                    affected_fields=["avg_stress_7d", "stress_trend_7d"],
                    suggested_scenario_types=["INCREASE_SLEEP", "REDUCE_WORKLOAD"],
                    confidence=0.90,
                ))

        # Check 6: Low confidence (from EngagementState if provided)
        if engagement_state is not None and engagement_state.avg_confidence_7d is not None:
            if engagement_state.avg_confidence_7d < 2.5:
                severity = self._classify_severity(
                    5.0 - engagement_state.avg_confidence_7d,  # Gap from 5
                    {"low": 2.0, "medium": 2.5, "high": 3.0, "critical": 4.0}
                )
                diagnoses.append(self._build_diagnosis(
                    issue_name="low_confidence",
                    severity=severity,
                    description=f"Average confidence is {engagement_state.avg_confidence_7d:.1f}/5.0",
                    affected_fields=["avg_confidence_7d"],
                    suggested_scenario_types=["REDUCE_WORKLOAD"],
                    confidence=0.75,
                ))

        return diagnoses

    def get_supported_scenarios(self) -> List[str]:
        """Return scenario types this agent can trigger."""
        return ["INCREASE_SLEEP", "REDUCE_WORKLOAD"]
