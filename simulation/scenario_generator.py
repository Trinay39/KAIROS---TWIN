"""
KAIROS-TWIN Phase 5: Scenario Generator.

Generates candidate counterfactual scenarios based on current student state.
Uses deterministic rules, not random generation.
"""
from __future__ import annotations
from typing import List, Dict, Any
from core.schemas import StudentTwinState
from simulation.scenario_schema import (
    Scenario, ScenarioType,
    create_move_assignment_scenario,
    create_reduce_workload_scenario,
    create_increase_study_time_scenario,
    create_increase_sleep_scenario,
    create_reduce_deadline_density_scenario,
)


class ScenarioGenerator:
    """
    Generates candidate scenarios based on current twin state.

    Rules (deterministic, not random):
    - High deadline density → workload redistribution scenarios
    - Sleep deficit → sleep improvement scenarios
    - Low study consistency → study schedule scenarios
    - High pending assignments → workload reduction scenarios
    - High stress + low confidence → recovery/sleep scenarios

    Each scenario is generated based on actual observed state,
    not random permutations.
    """

    # Thresholds for scenario generation
    THRESHOLD_HIGH_WORKLOAD = 0.7  # workload_pressure_score
    THRESHOLD_HIGH_DEADLINE_DENSITY = 0.6
    THRESHOLD_SLEEP_DEFICIT = 2.0  # hours
    THRESHOLD_LOW_STUDY_CONSISTENCY = 0.4
    THRESHOLD_HIGH_STRESS = 3.4  # avg_stress_7d is [1, 5] Likert
    THRESHOLD_LOW_CONFIDENCE = 2.5  # avg_confidence_7d is [1, 5] Likert
    THRESHOLD_HIGH_PENDING = 8

    @staticmethod
    def generate(
        twin_state: StudentTwinState,
        day: int,
        include_all: bool = False
    ) -> List[Scenario]:
        """
        Generate candidate scenarios for the current state.

        Args:
            twin_state: Current student state
            day: Current semester day
            include_all: If True, generate ALL possible scenarios
                        If False, generate only rule-based scenarios

        Returns:
            List of Scenario objects (may be empty)
        """
        scenarios = []

        # Rule 1: High workload → reduce workload
        if include_all or ScenarioGenerator._has_high_workload(twin_state):
            scenarios.extend(
                ScenarioGenerator._generate_workload_reduction(twin_state, day)
            )

        # Rule 2: High deadline density → reduce deadline density
        if include_all or ScenarioGenerator._has_high_deadline_density(twin_state):
            scenarios.append(
                create_reduce_deadline_density_scenario(day)
            )

        # Rule 3: Sleep deficit → increase sleep
        if include_all or ScenarioGenerator._has_sleep_deficit(twin_state):
            scenarios.extend(
                ScenarioGenerator._generate_sleep_improvement(twin_state, day)
            )

        # Rule 4: Low study consistency → increase study time
        if include_all or ScenarioGenerator._has_low_study_consistency(twin_state):
            scenarios.extend(
                ScenarioGenerator._generate_study_improvement(twin_state, day)
            )

        # Rule 5: High stress + low confidence → recovery focus
        if include_all or (
            ScenarioGenerator._has_high_stress(twin_state) and
            ScenarioGenerator._has_low_confidence(twin_state)
        ):
            scenarios.extend(
                ScenarioGenerator._generate_recovery_focus(twin_state, day)
            )

        return scenarios

    @staticmethod
    def _has_high_workload(state: StudentTwinState) -> bool:
        """Check if workload is high."""
        return (
            state.workload.workload_pressure_score_7d and
            state.workload.workload_pressure_score_7d > ScenarioGenerator.THRESHOLD_HIGH_WORKLOAD
        )

    @staticmethod
    def _has_high_deadline_density(state: StudentTwinState) -> bool:
        """Check if deadline density is high."""
        return (
            state.workload.deadline_density_trend_7d and
            state.workload.deadline_density_trend_7d > ScenarioGenerator.THRESHOLD_HIGH_DEADLINE_DENSITY
        )

    @staticmethod
    def _has_sleep_deficit(state: StudentTwinState) -> bool:
        """Check if sleep deficit exists."""
        return (
            state.recovery.sleep_deficit_7d_hours and
            state.recovery.sleep_deficit_7d_hours > ScenarioGenerator.THRESHOLD_SLEEP_DEFICIT
        )

    @staticmethod
    def _has_low_study_consistency(state: StudentTwinState) -> bool:
        """Check if study consistency is low."""
        return (
            state.behavioral.study_consistency_score and
            state.behavioral.study_consistency_score < ScenarioGenerator.THRESHOLD_LOW_STUDY_CONSISTENCY
        )

    @staticmethod
    def _has_high_stress(state: StudentTwinState) -> bool:
        """Check if stress is high."""
        return (
            state.engagement.avg_stress_7d and
            state.engagement.avg_stress_7d > ScenarioGenerator.THRESHOLD_HIGH_STRESS
        )

    @staticmethod
    def _has_low_confidence(state: StudentTwinState) -> bool:
        """Check if confidence is low."""
        return (
            state.engagement.avg_confidence_7d and
            state.engagement.avg_confidence_7d < ScenarioGenerator.THRESHOLD_LOW_CONFIDENCE
        )

    @staticmethod
    def _generate_workload_reduction(
        state: StudentTwinState,
        day: int
    ) -> List[Scenario]:
        """Generate workload reduction scenarios."""
        scenarios = []

        # Generate 3 levels of reduction
        for reduction_pct in [10, 20, 30]:
            scenario = create_reduce_workload_scenario(reduction_pct, day)
            scenarios.append(scenario)

        return scenarios

    @staticmethod
    def _generate_sleep_improvement(
        state: StudentTwinState,
        day: int
    ) -> List[Scenario]:
        """Generate sleep improvement scenarios."""
        scenarios = []

        # Target sleep levels: 7.5h, 8h, 8.5h
        for target_hours in [7.5, 8.0, 8.5]:
            scenario = create_increase_sleep_scenario(target_hours, day)
            scenarios.append(scenario)

        return scenarios

    @staticmethod
    def _generate_study_improvement(
        state: StudentTwinState,
        day: int
    ) -> List[Scenario]:
        """Generate study time improvement scenarios."""
        scenarios = []

        # Additional study hours: 1, 2, 3 hours per day
        for hours in [1.0, 2.0, 3.0]:
            scenario = create_increase_study_time_scenario(hours, 7, day)
            scenarios.append(scenario)

        return scenarios

    @staticmethod
    def _generate_recovery_focus(
        state: StudentTwinState,
        day: int
    ) -> List[Scenario]:
        """Generate recovery-focused scenarios."""
        scenarios = []

        # Combine sleep + reduced workload
        scenarios.append(create_increase_sleep_scenario(8.0, day))
        scenarios.extend(ScenarioGenerator._generate_workload_reduction(state, day))

        return scenarios

    @staticmethod
    def get_generation_rules() -> Dict[str, str]:
        """Return documentation of generation rules."""
        return {
            'high_workload': (
                f"If workload_pressure_score > {ScenarioGenerator.THRESHOLD_HIGH_WORKLOAD}: "
                "generate 3 workload reduction scenarios (10%, 20%, 30%)"
            ),
            'high_deadline_density': (
                f"If deadline_density_trend > {ScenarioGenerator.THRESHOLD_HIGH_DEADLINE_DENSITY}: "
                "generate 1 deadline redistribution scenario"
            ),
            'sleep_deficit': (
                f"If sleep_deficit > {ScenarioGenerator.THRESHOLD_SLEEP_DEFICIT}h: "
                "generate 3 sleep improvement scenarios (7.5h, 8h, 8.5h)"
            ),
            'low_study_consistency': (
                f"If study_consistency < {ScenarioGenerator.THRESHOLD_LOW_STUDY_CONSISTENCY}: "
                "generate 3 study improvement scenarios (1h, 2h, 3h/day)"
            ),
            'stress_confidence': (
                f"If stress > {ScenarioGenerator.THRESHOLD_HIGH_STRESS} AND "
                f"confidence < {ScenarioGenerator.THRESHOLD_LOW_CONFIDENCE}: "
                "generate recovery-focused scenarios (sleep + workload reduction)"
            ),
        }
