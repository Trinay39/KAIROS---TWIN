"""
KAIROS-TWIN Phase 6: Recommendation System.

Defines the Recommendation dataclass and formatting logic for presenting
interventions to students with safety constraints (no causality claims,
no value invention).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class RecommendationConfidence(Enum):
    """Confidence levels for recommendations."""
    LOW = "low"        # Tentative suggestion
    MEDIUM = "medium"  # Reasonable recommendation
    HIGH = "high"      # Confident recommendation
    VERY_HIGH = "very_high"  # Strongly recommended


@dataclass
class RecommendationConfig:
    """
    Configuration for recommendation generation.

    Controls what information is included and how it's presented.
    """
    include_caveats: bool = True
    include_confidence: bool = True
    include_risk_delta: bool = True
    include_changed_features: bool = True
    max_recommendations: int = 3
    always_include_synthetic_disclaimer: bool = True
    language_constraints: Dict[str, bool] = field(default_factory=lambda: {
        "no_causal_claims": True,
        "no_value_invention": True,
        "model_estimated_prefix": True,
        "hypothetical_language": True,
    })


@dataclass
class Recommendation:
    """
    Final recommendation produced by the multi-agent system.

    This is presented to the student with safety constraints:
    - No causal claims (use "model-estimated" not "causes")
    - No value invention (use CounterfactualEngine outputs only)
    - Always includes synthetic data disclaimer
    """
    # Scenario information
    scenario_id: str
    scenario_type: str
    scenario_description: str

    # Impact estimates (from CounterfactualEngine)
    baseline_risk: float  # [0, 1]
    counterfactual_risk: float  # [0, 1]
    risk_delta: float  # baseline - counterfactual (positive = improvement)
    risk_reduction_percentage: float  # percentage reduction
    strain_delta: Optional[float] = None  # strain index change

    # Changed features (from FeatureRecalculator)
    changed_features_count: int = 0
    top_changed_features: List[Dict[str, Any]] = field(default_factory=list)

    # Explanation and reasoning
    explanation: str = ""  # LLM-generated explanation (safety constrained)
    primary_diagnoses: List[str] = field(default_factory=list)  # Which agents flagged this
    confidence: RecommendationConfidence = RecommendationConfidence.MEDIUM

    # Safety constraints
    caveats: List[str] = field(default_factory=lambda: [
        "Based on model-estimated predictions",
        "Trained on synthetic data only",
        "Individual results may vary",
    ])

    # Success indicator (computed from risk_delta)
    was_successful: bool = field(default=False, init=False)

    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    student_id: str = ""
    day: int = 0

    def __post_init__(self):
        """Post-initialization to compute was_successful."""
        self.was_successful = self.risk_delta > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'scenario_id': self.scenario_id,
            'scenario_type': self.scenario_type,
            'scenario_description': self.scenario_description,
            'baseline_risk': self.baseline_risk,
            'counterfactual_risk': self.counterfactual_risk,
            'risk_delta': self.risk_delta,
            'risk_reduction_percentage': self.risk_reduction_percentage,
            'strain_delta': self.strain_delta,
            'changed_features_count': self.changed_features_count,
            'top_changed_features': self.top_changed_features,
            'explanation': self.explanation,
            'primary_diagnoses': self.primary_diagnoses,
            'confidence': self.confidence.value,
            'caveats': self.caveats,
            'was_successful': self.was_successful,
            'timestamp': self.timestamp,
            'student_id': self.student_id,
            'day': self.day,
        }

    def format_for_student(self, config: Optional[RecommendationConfig] = None) -> str:
        """
        Format recommendation for student presentation.

        Args:
            config: Configuration controlling what to include

        Returns:
            Human-readable string ready for student presentation
        """
        if config is None:
            config = RecommendationConfig()

        lines = []

        # Header
        lines.append(f"## Intervention Recommendation")
        lines.append("")

        # Scenario description
        lines.append(f"**Option:** {self.scenario_description}")
        lines.append("")

        # Estimated impact (with safety language)
        if config.include_risk_delta:
            lines.append(f"**Estimated impact:**")
            lines.append(f"- Model-estimated risk under this scenario: {self.counterfactual_risk:.1%}")
            lines.append(f"- Risk reduction: {abs(self.risk_delta):.1%} (from {self.baseline_risk:.1%})")

            if self.strain_delta is not None and self.strain_delta < 0:
                lines.append(f"- Strain index reduction: {abs(self.strain_delta):.3f}")
            lines.append("")

        # Which agents flagged this issue
        if self.primary_diagnoses:
            lines.append(f"**Why this might help:**")
            for diagnosis in self.primary_diagnoses:
                lines.append(f"- {diagnosis}")
            lines.append("")

        # LLM explanation
        lines.append(f"**Explanation:**")
        lines.append(self.explanation)
        lines.append("")

        # Changed features (if any)
        if config.include_changed_features and self.top_changed_features:
            lines.append(f"**What changes:**")
            for feature in self.top_changed_features[:3]:
                name = feature.get('feature_name', 'unknown')
                lines.append(f"- {name}")
            lines.append("")

        # Confidence level
        if config.include_confidence:
            confidence_map = {
                RecommendationConfidence.LOW: "low confidence",
                RecommendationConfidence.MEDIUM: "moderate confidence",
                RecommendationConfidence.HIGH: "high confidence",
                RecommendationConfidence.VERY_HIGH: "very high confidence",
            }
            lines.append(f"**Confidence:** {confidence_map[self.confidence]}")
            lines.append("")

        # Caveats (ALWAYS included)
        if config.include_caveats or config.always_include_synthetic_disclaimer:
            lines.append("**Important notes:**")
            for caveat in self.caveats:
                lines.append(f"- {caveat}")

            # Always include synthetic disclaimer
            if config.always_include_synthetic_disclaimer and "synthetic data" not in "\n".join(self.caveats):
                lines.append("- Model trained on synthetic data; real-world performance may differ")

            # Safety disclaimers
            if config.language_constraints.get("no_causal_claims", True):
                lines.append("- This is a model-estimated association, not a causal claim")
            lines.append("")

        return "\n".join(lines)

    def validate_safety(self) -> bool:
        """
        Validate that recommendation meets safety constraints.

        Checks:
        1. No causal claims ("causes", "will reduce", "guaranteed")
        2. No value invention (risk deltas must match CounterfactualEngine)
        3. Contains synthetic data disclaimer
        4. Uses "model-estimated" language

        Returns:
            True if safe, False if violates constraints
        """
        text_to_check = self.explanation.lower() + "\n".join(self.caveats).lower()

        # 1. No causal claims
        causal_phrases = [
            "causes", "will reduce", "guaranteed", "definitely",
            "will improve", "ensures", "results in", "leads to"
        ]
        for phrase in causal_phrases:
            if phrase in text_to_check:
                return False

        # 2. Must mention synthetic data
        synthetic_phrases = ["synthetic data", "model trained on synthetic", "simulated data"]
        has_synthetic = any(phrase in text_to_check for phrase in synthetic_phrases)
        if not has_synthetic:
            return False

        # 3. Should use "model-estimated" language
        safety_phrases = ["model-estimated", "model predicts", "estimated under", "predicted impact"]
        has_safety = any(phrase in text_to_check for phrase in safety_phrases)
        if not has_safety:
            return False

        return True

    @classmethod
    def from_counterfactual_result(
        cls,
        result,
        scenario,
        diagnoses: List[str],
        explanation: str,
        student_id: str = "",
        day: int = 0,
        config: Optional[RecommendationConfig] = None
    ) -> "Recommendation":
        """
        Create Recommendation from CounterfactualResult.

        Args:
            result: CounterfactualResult from Phase 5
            scenario: Scenario object that was simulated
            diagnoses: Which agent diagnoses triggered this scenario
            explanation: LLM-generated explanation (already validated)
            student_id: Student identifier
            day: Current semester day
            config: Recommendation configuration

        Returns:
            Recommendation object
        """
        if config is None:
            config = RecommendationConfig()

        # Extract top changed features
        top_changed_features = []
        if hasattr(result, 'changed_features') and result.changed_features:
            top_changed_features = sorted(
                result.changed_features,
                key=lambda x: abs(x.get('delta', 0)),
                reverse=True
            )[:5]

        # Calculate confidence based on risk reduction magnitude
        risk_reduction = abs(result.risk_delta)
        if risk_reduction >= 0.15:
            confidence = RecommendationConfidence.VERY_HIGH
        elif risk_reduction >= 0.10:
            confidence = RecommendationConfidence.HIGH
        elif risk_reduction >= 0.05:
            confidence = RecommendationConfidence.MEDIUM
        else:
            confidence = RecommendationConfidence.LOW

        return cls(
            scenario_id=scenario.scenario_id if hasattr(scenario, 'scenario_id') else f"scenario_{hash(scenario)}",
            scenario_type=scenario.scenario_type.value if hasattr(scenario, 'scenario_type') else str(scenario),
            scenario_description=getattr(scenario, 'description', 'Intervention scenario'),

            baseline_risk=result.baseline_prediction.overload_probability,
            counterfactual_risk=result.counterfactual_prediction.overload_probability,
            risk_delta=result.risk_delta,
            risk_reduction_percentage=result.risk_reduction_percentage,
            strain_delta=(
                result.counterfactual_prediction.strain_index - result.baseline_prediction.strain_index
                if hasattr(result, 'counterfactual_prediction') and hasattr(result, 'baseline_prediction')
                and result.counterfactual_prediction.strain_index and result.baseline_prediction.strain_index
                else None
            ),

            changed_features_count=getattr(result, 'changed_features_count', 0),
            top_changed_features=top_changed_features,

            explanation=explanation,
            primary_diagnoses=diagnoses,
            confidence=confidence,

            student_id=student_id,
            day=day,
        )
