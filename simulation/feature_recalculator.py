"""
KAIROS-TWIN Phase 5: Feature Recalculator.

Recomputes all 46 ML features after state modification.
Uses Phase 3 FeatureEngine to ensure consistency with training.
"""
from __future__ import annotations
from typing import Tuple, List, Dict, Any
import numpy as np

from core.schemas import StudentTwinState
from core.feature_engine import FeatureEngine
from ml.feature_contract import (
    EXPECTED_FEATURE_COUNT as CONTRACT_FEATURE_COUNT,
    raw_feature_order,
    raw_mapping_to_array,
    validate_raw_feature_mapping,
)


class FeatureRecalculator:
    """
    Recomputes 46 features after state modification.

    CRITICAL: Uses Phase 3 FeatureEngine.extract() to ensure features
    are recalculated consistently with training data.

    Process:
    1. Baseline state → FeatureEngine → 46 features (baseline_features)
    2. Scenario modifies state → modified_state
    3. Modified state → FeatureEngine → 46 features (counterfactual_features)
    4. Compare feature vectors element-wise

    Invariants:
    - Always exactly 46 features
    - Feature ordering matches Phase 4 training
    - No manual feature modification (all via FeatureEngine)
    """

    EXPECTED_FEATURE_COUNT = CONTRACT_FEATURE_COUNT

    @staticmethod
    def extract_feature_dict(twin_state: StudentTwinState) -> Dict[str, float]:
        """
        Extract and validate raw feature mapping from StudentTwinState.

        Raises:
            FeatureContractError: If the FeatureEngine output does not exactly
                match the production feature contract.
        """
        engine = FeatureEngine()
        features_dict = engine.extract_features(twin_state)
        validate_raw_feature_mapping(features_dict)
        return features_dict

    @staticmethod
    def extract_features(twin_state: StudentTwinState) -> np.ndarray:
        """
        Extract 46 features from StudentTwinState.

        Args:
            twin_state: Student state at time t

        Returns:
            Feature vector (46,) with dtype float64

        Raises:
            ValueError: If feature count != 46
        """
        features_dict = FeatureRecalculator.extract_feature_dict(twin_state)
        features = raw_mapping_to_array(features_dict).ravel().astype(np.float64)

        if len(features) != FeatureRecalculator.EXPECTED_FEATURE_COUNT:
            raise ValueError(
                f"Expected {FeatureRecalculator.EXPECTED_FEATURE_COUNT} features, "
                f"got {len(features)}"
            )

        return features

    @staticmethod
    def get_feature_names() -> List[str]:
        """Get ordered feature names (matches Phase 4 training)."""
        return raw_feature_order()

    @staticmethod
    def compare_features(
        baseline_features: np.ndarray,
        counterfactual_features: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Compare two feature vectors.

        Args:
            baseline_features: Baseline feature vector (46,)
            counterfactual_features: Counterfactual feature vector (46,)

        Returns:
            Dict with:
            - changed_count: number of features that changed
            - unchanged_count: number that stayed same
            - changes: list of (feature_idx, feature_name, baseline_val, cf_val, delta)
            - max_delta: largest absolute change
            - mean_delta: average absolute change
        """
        if len(baseline_features) != FeatureRecalculator.EXPECTED_FEATURE_COUNT:
            raise ValueError("Baseline feature count mismatch")

        if len(counterfactual_features) != FeatureRecalculator.EXPECTED_FEATURE_COUNT:
            raise ValueError("Counterfactual feature count mismatch")

        feature_names = FeatureRecalculator.get_feature_names()
        deltas = np.abs(counterfactual_features - baseline_features)

        changes = []
        for i, (base_val, cf_val) in enumerate(
            zip(baseline_features, counterfactual_features)
        ):
            if base_val != cf_val:
                changes.append({
                    'feature_idx': i,
                    'feature_name': feature_names[i],
                    'baseline_value': float(base_val),
                    'counterfactual_value': float(cf_val),
                    'delta': float(cf_val - base_val),
                    'abs_delta': float(np.abs(cf_val - base_val)),
                })

        return {
            'changed_count': len(changes),
            'unchanged_count': FeatureRecalculator.EXPECTED_FEATURE_COUNT - len(changes),
            'changes': changes,
            'max_delta': float(np.max(deltas)) if len(changes) > 0 else 0.0,
            'mean_delta': float(np.mean(deltas[deltas > 0])) if len(changes) > 0 else 0.0,
        }

    @staticmethod
    def verify_feature_integrity(features: np.ndarray) -> Tuple[bool, str]:
        """
        Verify feature vector integrity.

        Args:
            features: Feature vector

        Returns:
            (is_valid, message)
        """
        # Check shape
        if len(features) != FeatureRecalculator.EXPECTED_FEATURE_COUNT:
            return False, f"Shape mismatch: expected (46,), got ({len(features)},)"

        # Check for NaN
        if np.any(np.isnan(features)):
            nan_indices = np.where(np.isnan(features))[0]
            return False, f"NaN values at indices: {nan_indices.tolist()}"

        # Check for Inf
        if np.any(np.isinf(features)):
            inf_indices = np.where(np.isinf(features))[0]
            return False, f"Inf values at indices: {inf_indices.tolist()}"

        # Check dtype
        if features.dtype != np.float64:
            return False, f"Expected float64, got {features.dtype}"

        return True, "OK"

    @staticmethod
    def log_feature_changes(
        comparison: Dict[str, Any],
        scenario_description: str = ""
    ) -> str:
        """
        Generate human-readable summary of feature changes.

        Args:
            comparison: Output from compare_features()
            scenario_description: Scenario description for context

        Returns:
            Formatted string summary
        """
        lines = []
        lines.append(f"Feature Changes Summary")
        if scenario_description:
            lines.append(f"Scenario: {scenario_description}")
        lines.append(f"  Changed: {comparison['changed_count']}/46")
        lines.append(f"  Unchanged: {comparison['unchanged_count']}/46")
        lines.append(f"  Max delta: {comparison['max_delta']:.6f}")
        lines.append(f"  Mean delta: {comparison['mean_delta']:.6f}")

        if comparison['changes']:
            lines.append(f"\n  Top 5 changes:")
            sorted_changes = sorted(
                comparison['changes'],
                key=lambda x: x['abs_delta'],
                reverse=True
            )[:5]
            for change in sorted_changes:
                lines.append(
                    f"    {change['feature_name']}: "
                    f"{change['baseline_value']:.4f} → {change['counterfactual_value']:.4f} "
                    f"(Δ {change['delta']:+.4f})"
                )

        return "\n".join(lines)
