"""
KAIROS-TWIN Phase 5: Scenario Ranker.

Ranks scenarios by estimated impact using transparent scoring function.
"""
from __future__ import annotations
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

from simulation.counterfactual_engine import CounterfactualResult


@dataclass
class RankedScenario:
    """Ranked scenario with score and components."""

    rank: int
    scenario_id: str
    scenario_description: str
    score: float
    risk_reduction_component: float
    strain_reduction_component: float
    feasibility_component: float
    result: CounterfactualResult

    @property
    def scenario(self) -> Scenario:
        """Delegating property so callers can use ranked_scenario.scenario."""
        return self.result.scenario

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'rank': self.rank,
            'scenario_id': self.scenario_id,
            'scenario_description': self.scenario_description,
            'overall_score': float(self.score),
            'risk_reduction_component': float(self.risk_reduction_component),
            'strain_reduction_component': float(self.strain_reduction_component),
            'feasibility_component': float(self.feasibility_component),
            'baseline_risk': float(self.result.baseline_prediction.overload_probability),
            'counterfactual_risk': float(self.result.counterfactual_prediction.overload_probability),
            'estimated_risk_reduction_pct': float(self.result.risk_reduction_percentage),
        }


class ScenarioRanker:
    """
    Ranks scenarios using transparent multi-factor scoring.

    Scoring function:
        score = 0.60 × normalized_risk_reduction
              + 0.25 × normalized_strain_reduction
              + 0.15 × feasibility_score

    Weights are design parameters, NOT learned causal weights.
    """

    # Configurable weights (design parameters, not learned)
    WEIGHT_RISK = 0.60
    WEIGHT_STRAIN = 0.25
    WEIGHT_FEASIBILITY = 0.15

    @staticmethod
    def rank(
        results: List[CounterfactualResult],
        weights: Dict[str, float] = None
    ) -> List[RankedScenario]:
        """
        Rank counterfactual results.

        Args:
            results: List of CounterfactualResult objects
            weights: Optional custom weights dict with keys:
                    'risk', 'strain', 'feasibility'
                    Defaults to class weights if not provided

        Returns:
            Sorted list of RankedScenario (best first)
        """
        if not results:
            return []

        # Use provided weights or defaults
        if weights is None:
            weights = {
                'risk': ScenarioRanker.WEIGHT_RISK,
                'strain': ScenarioRanker.WEIGHT_STRAIN,
                'feasibility': ScenarioRanker.WEIGHT_FEASIBILITY,
            }

        # Normalize components
        risk_values = [max(r.risk_reduction_percentage, 0) for r in results]
        strain_values = [
            max(r.strain_delta or 0, 0) if r.strain_delta else 0
            for r in results
        ]

        max_risk = max(risk_values) if risk_values else 1.0
        max_strain = max(strain_values) if strain_values else 1.0

        # Score each result
        scored = []
        for i, result in enumerate(results):
            risk_norm = (
                risk_values[i] / max_risk if max_risk > 0 else 0
            )
            strain_norm = (
                strain_values[i] / max_strain if max_strain > 0 else 0
            )
            feasibility_score = ScenarioRanker._compute_feasibility(result)

            overall_score = (
                weights['risk'] * risk_norm +
                weights['strain'] * strain_norm +
                weights['feasibility'] * feasibility_score
            )

            scored.append((
                i,
                result,
                risk_norm,
                strain_norm,
                feasibility_score,
                overall_score
            ))

        # Sort by score (descending)
        scored.sort(key=lambda x: x[5], reverse=True)

        # Create RankedScenario objects
        ranked = []
        for rank, (_, result, risk_comp, strain_comp, feas_comp, score) in enumerate(scored, 1):
            ranked_scenario = RankedScenario(
                rank=rank,
                scenario_id=result.scenario.scenario_id,
                scenario_description=result.scenario.description,
                score=float(score),
                risk_reduction_component=float(risk_comp),
                strain_reduction_component=float(strain_comp),
                feasibility_component=float(feas_comp),
                result=result,
            )
            ranked.append(ranked_scenario)

        return ranked

    @staticmethod
    def _compute_feasibility(result: CounterfactualResult) -> float:
        """
        Compute feasibility score for a scenario.

        Factors:
        - Requires instructor approval → lower score
        - Requires student action only → higher score
        - High risk level → lower score
        - Low risk level → higher score

        Args:
            result: CounterfactualResult

        Returns:
            Feasibility score in [0, 1]
        """
        feasibility = 0.5  # Base score

        metadata = result.scenario.feasibility_metadata

        # Instructor approval penalty
        if metadata.get('requires_instructor_approval'):
            feasibility -= 0.15
        elif metadata.get('requires_instructor_coordination'):
            feasibility -= 0.10
        elif metadata.get('requires_student_action'):
            feasibility += 0.10

        # Risk level adjustment
        risk_level = metadata.get('risk_level', 'medium')
        if risk_level == 'low':
            feasibility += 0.15
        elif risk_level == 'medium':
            feasibility += 0.0
        elif risk_level == 'high':
            feasibility -= 0.10
        elif risk_level == 'very_high':
            feasibility -= 0.25

        # Sustainability
        sustainability = metadata.get('sustainability')
        if sustainability == 'high':
            feasibility += 0.10
        elif sustainability == 'uncertain':
            feasibility -= 0.05

        # Clamp to [0, 1]
        return max(0.0, min(1.0, feasibility))

    @staticmethod
    def get_top_k(
        ranked: List[RankedScenario],
        k: int = 5
    ) -> List[RankedScenario]:
        """Get top k scenarios."""
        return ranked[:k]

    @staticmethod
    def format_ranking_report(ranked: List[RankedScenario]) -> str:
        """Generate text report of ranked scenarios."""
        lines = []
        lines.append("SCENARIO RANKING REPORT")
        lines.append("=" * 70)
        lines.append(
            f"{'Rank':<6} {'Score':<8} {'Risk Δ':<10} {'Strain Δ':<10} {'Feasibility':<12} Scenario"
        )
        lines.append("-" * 70)

        for ranked_scenario in ranked[:10]:  # Top 10
            lines.append(
                f"{ranked_scenario.rank:<6} "
                f"{ranked_scenario.score:<8.3f} "
                f"{ranked_scenario.risk_reduction_component:<10.3f} "
                f"{ranked_scenario.strain_reduction_component:<10.3f} "
                f"{ranked_scenario.feasibility_component:<12.3f} "
                f"{ranked_scenario.scenario_description[:35]}"
            )

        lines.append("=" * 70)
        lines.append("Note: Scores are design parameters for ranking, not causal weights.")

        return "\n".join(lines)

    @staticmethod
    def get_ranking_config() -> Dict[str, Any]:
        """Return ranking configuration for reproducibility."""
        return {
            'method': 'weighted_multi_factor',
            'weights': {
                'risk_reduction': ScenarioRanker.WEIGHT_RISK,
                'strain_reduction': ScenarioRanker.WEIGHT_STRAIN,
                'feasibility': ScenarioRanker.WEIGHT_FEASIBILITY,
            },
            'normalization': 'max_value',
            'note': 'Weights are design parameters for ranking, not learned causal weights.',
        }
