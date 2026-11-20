"""
KAIROS-TWIN Phase 5: Counterfactual Engine.

Simulates counterfactual scenarios and computes prediction deltas.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from dataclasses import dataclass
import numpy as np

from core.schemas import StudentTwinState
from simulation.prediction_service import PredictionService, PredictionSnapshot
from simulation.scenario_schema import Scenario
from simulation.state_modifier import StateModifier
from simulation.feature_recalculator import FeatureRecalculator


@dataclass
class CounterfactualResult:
    """Result of counterfactual simulation."""

    scenario: Scenario
    baseline_prediction: PredictionSnapshot
    counterfactual_prediction: PredictionSnapshot
    risk_delta: float  # counterfactual - baseline
    risk_reduction_percentage: float  # (baseline - counterfactual) / baseline * 100
    baseline_strain: Optional[float] = None
    counterfactual_strain: Optional[float] = None
    strain_delta: Optional[float] = None
    changed_features: Dict[str, tuple] = None  # {feature_name: (baseline, cf)}
    unchanged_features: int = 0
    feature_comparison: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'scenario_id': self.scenario.scenario_id,
            'scenario_type': self.scenario.scenario_type.value,
            'scenario_description': self.scenario.description,
            'baseline_probability': float(self.baseline_prediction.overload_probability),
            'counterfactual_probability': float(self.counterfactual_prediction.overload_probability),
            'risk_delta': float(self.risk_delta),
            'risk_reduction_percentage': float(self.risk_reduction_percentage),
            'baseline_strain': float(self.baseline_strain) if self.baseline_strain is not None else None,
            'counterfactual_strain': float(self.counterfactual_strain) if self.counterfactual_strain is not None else None,
            'strain_delta': float(self.strain_delta) if self.strain_delta is not None else None,
            'changed_features_count': len(self.changed_features) if self.changed_features else 0,
            'unchanged_features_count': self.unchanged_features,
            'interpretation': self._get_interpretation(),
        }

    def _get_interpretation(self) -> str:
        """Generate human-readable interpretation."""
        if self.risk_reduction_percentage >= 10:
            return f"Substantial reduction: {self.risk_reduction_percentage:.1f}%"
        elif self.risk_reduction_percentage > 0:
            return f"Modest reduction: {self.risk_reduction_percentage:.1f}%"
        elif self.risk_reduction_percentage == 0:
            return "No change"
        else:
            return f"Risk increase: {abs(self.risk_reduction_percentage):.1f}%"

    def get_summary(self) -> str:
        """Generate text summary."""
        lines = []
        lines.append(f"Scenario: {self.scenario.description}")
        lines.append(f"Baseline Risk: {self.baseline_prediction.overload_probability:.1%}")
        lines.append(f"Estimated Risk: {self.counterfactual_prediction.overload_probability:.1%}")
        lines.append(f"Estimated Relative Reduction: {self.risk_reduction_percentage:.1f}%")

        if self.changed_features:
            lines.append(f"\nChanged Features: {len(self.changed_features)}")
            for fname, (base_val, cf_val) in list(self.changed_features.items())[:3]:
                lines.append(f"  - {fname}: {base_val:.4f} → {cf_val:.4f}")

        lines.append(f"\nInterpretation:")
        lines.append(f"  The model estimates {self._get_interpretation().lower()} under this hypothetical scenario.")

        return "\n".join(lines)


class CounterfactualEngine:
    """
    Simulates counterfactual scenarios and computes deltas.

    Process:
    1. Predict baseline (original state)
    2. Clone state, apply scenario modifications
    3. Recompute all 46 features from modified state
    4. Predict counterfactual
    5. Compute deltas and return CounterfactualResult
    """

    def __init__(self, prediction_service: PredictionService):
        """
        Initialize counterfactual engine.

        Args:
            prediction_service: Loaded PredictionService for predictions
        """
        self.prediction_service = prediction_service
        self.feature_recalculator = FeatureRecalculator()

    def simulate(
        self,
        baseline_state: StudentTwinState,
        scenario: Scenario,
        day: int = 0
    ) -> CounterfactualResult:
        """
        Simulate a counterfactual scenario.

        Args:
            baseline_state: Original student state (not modified)
            scenario: Scenario to simulate
            day: Semester day for context

        Returns:
            CounterfactualResult with predictions and deltas

        Raises:
            ValueError: If temporal constraints violated
        """
        # Verify baseline state unchanged before/after
        state_copy_before = StateModifier.clone(baseline_state)

        # Predict baseline
        baseline_pred = self.prediction_service.predict(baseline_state, day)
        baseline_features = FeatureRecalculator.extract_features(baseline_state)

        # Verify baseline unchanged
        assert StateModifier.verify_unchanged(baseline_state, state_copy_before), \
            "Baseline state was modified!"

        # Apply scenario to cloned state
        counterfactual_state = self._apply_scenario(
            baseline_state,
            scenario,
            day
        )

        # Extract counterfactual features
        cf_features = FeatureRecalculator.extract_features(counterfactual_state)

        # Verify baseline still unchanged
        assert StateModifier.verify_unchanged(baseline_state, state_copy_before), \
            "Baseline state was modified during counterfactual!"

        # Predict counterfactual
        cf_pred = self.prediction_service.predict(counterfactual_state, day)

        # Compare features
        feature_comparison = FeatureRecalculator.compare_features(
            baseline_features,
            cf_features
        )

        # Build changed_features dict
        changed_features = {}
        feature_names = FeatureRecalculator.get_feature_names()
        for change in feature_comparison['changes']:
            fname = change['feature_name']
            changed_features[fname] = (
                change['baseline_value'],
                change['counterfactual_value']
            )

        # Compute deltas
        risk_delta = cf_pred.overload_probability - baseline_pred.overload_probability

        # Avoid division by zero
        if baseline_pred.overload_probability > 0:
            risk_reduction_pct = (
                (baseline_pred.overload_probability - cf_pred.overload_probability)
                / baseline_pred.overload_probability * 100
            )
        else:
            risk_reduction_pct = 0.0

        strain_delta = None
        if baseline_pred.strain_index and cf_pred.strain_index:
            strain_delta = cf_pred.strain_index - baseline_pred.strain_index

        result = CounterfactualResult(
            scenario=scenario,
            baseline_prediction=baseline_pred,
            counterfactual_prediction=cf_pred,
            risk_delta=float(risk_delta),
            risk_reduction_percentage=float(risk_reduction_pct),
            baseline_strain=baseline_pred.strain_index,
            counterfactual_strain=cf_pred.strain_index,
            strain_delta=float(strain_delta) if strain_delta else None,
            changed_features=changed_features,
            unchanged_features=feature_comparison['unchanged_count'],
            feature_comparison=feature_comparison,
        )

        return result

    def _apply_scenario(
        self,
        baseline_state: StudentTwinState,
        scenario: Scenario,
        day: int
    ) -> StudentTwinState:
        """
        Apply scenario modifications to a cloned state.

        Args:
            baseline_state: Original state
            scenario: Scenario to apply
            day: Current semester day

        Returns:
            Modified state with scenario applied

        Raises:
            ValueError: If scenario violates temporal constraints
        """
        from simulation.scenario_schema import ScenarioType

        # Clone the state
        modified_state = StateModifier.clone(baseline_state)

        scenario_type = scenario.scenario_type

        # Route to appropriate handler
        if scenario_type == ScenarioType.MOVE_ASSIGNMENT:
            return self._apply_move_assignment(modified_state, scenario, day)

        elif scenario_type == ScenarioType.REMOVE_ASSIGNMENT:
            return self._apply_remove_assignment(modified_state, scenario, day)

        elif scenario_type == ScenarioType.REDUCE_WORKLOAD:
            return self._apply_reduce_workload(modified_state, scenario, day)

        elif scenario_type == ScenarioType.INCREASE_STUDY_TIME:
            return self._apply_increase_study_time(modified_state, scenario, day)

        elif scenario_type == ScenarioType.INCREASE_SLEEP:
            return self._apply_increase_sleep(modified_state, scenario, day)

        elif scenario_type == ScenarioType.REDUCE_DEADLINE_DENSITY:
            return self._apply_reduce_deadline_density(modified_state, scenario, day)

        else:
            raise ValueError(f"Unknown scenario type: {scenario_type}")

    def _apply_move_assignment(
        self,
        state: StudentTwinState,
        scenario: Scenario,
        day: int
    ) -> StudentTwinState:
        """Apply MOVE_ASSIGNMENT scenario."""
        # This is a placeholder; real implementation would modify workload state
        # For now, reduce pending count slightly and adjust deadline density
        params = scenario.parameters

        from_day = params.get('from_day', day + 1)
        to_day = params.get('to_day', day + 7)

        if from_day <= day or to_day <= day:
            raise ValueError(
                f"Cannot move assignment to past. Current day: {day}, "
                f"new date: {to_day}"
            )

        # Reduce deadline density near from_day, increase near to_day
        # This is simplified; real implementation would track assignments
        if state.workload.deadline_density_trend_7d:
            state.workload.deadline_density_trend_7d *= 0.9

        return state

    def _apply_remove_assignment(
        self,
        state: StudentTwinState,
        scenario: Scenario,
        day: int
    ) -> StudentTwinState:
        """Apply REMOVE_ASSIGNMENT scenario."""
        # Reduce pending assignment count
        if state.workload.pending_assignment_count > 0:
            state.workload.pending_assignment_count -= 1

        # Reduce workload pressure
        if state.workload.workload_pressure_score_7d:
            state.workload.workload_pressure_score_7d *= 0.85

        return state

    def _apply_reduce_workload(
        self,
        state: StudentTwinState,
        scenario: Scenario,
        day: int
    ) -> StudentTwinState:
        """Apply REDUCE_WORKLOAD scenario."""
        params = scenario.parameters
        reduction_pct = params.get('reduction_pct', 0.1)

        # Reduce pending assignments
        if state.workload.pending_assignment_count > 0:
            state.workload.pending_assignment_count = max(
                0,
                int(state.workload.pending_assignment_count * (1 - reduction_pct / 100))
            )

        # Reduce workload pressure
        if state.workload.workload_pressure_score_7d:
            state.workload.workload_pressure_score_7d *= (1 - reduction_pct / 100)

        return state

    def _apply_increase_study_time(
        self,
        state: StudentTwinState,
        scenario: Scenario,
        day: int
    ) -> StudentTwinState:
        """Apply INCREASE_STUDY_TIME scenario."""
        params = scenario.parameters
        hours_per_day = params.get('hours_per_day', 1.0)

        # Increase study hours
        if state.behavioral.avg_study_hours_7d:
            state.behavioral.avg_study_hours_7d += hours_per_day

        # Improve study consistency
        if state.behavioral.study_consistency_score:
            state.behavioral.study_consistency_score = min(
                1.0,
                state.behavioral.study_consistency_score + 0.1
            )

        # Reduce effort-study gap
        if state.workload.effort_study_gap_7d:
            state.workload.effort_study_gap_7d *= 0.8

        return state

    def _apply_increase_sleep(
        self,
        state: StudentTwinState,
        scenario: Scenario,
        day: int
    ) -> StudentTwinState:
        """Apply INCREASE_SLEEP scenario."""
        params = scenario.parameters
        target_sleep = params.get('hours_per_night', 8.0)

        # Update sleep metrics
        state.recovery.avg_sleep_hours_7d = target_sleep

        # Reduce sleep deficit
        if state.recovery.sleep_deficit_7d_hours:
            state.recovery.sleep_deficit_7d_hours = max(
                0,
                state.recovery.sleep_deficit_7d_hours - 2.0
            )

        # Improve recovery score
        state.recovery.recovery_score_7d = min(
            1.0,
            (target_sleep / 8.0) * 0.8 + 0.2
        )

        return state

    def _apply_reduce_deadline_density(
        self,
        state: StudentTwinState,
        scenario: Scenario,
        day: int
    ) -> StudentTwinState:
        """Apply REDUCE_DEADLINE_DENSITY scenario."""
        # Reduce deadline density
        if state.workload.deadline_density_trend_7d:
            state.workload.deadline_density_trend_7d *= 0.7

        # Reduce workload pressure
        if state.workload.workload_pressure_score_7d:
            state.workload.workload_pressure_score_7d *= 0.75

        return state
