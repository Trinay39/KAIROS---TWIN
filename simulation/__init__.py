"""
KAIROS-TWIN Phase 5: Counterfactual Digital Twin + Prediction Service.

This package implements counterfactual simulation for academic overload prediction.
It answers: "Given the student's current state, what happens to predicted overload risk
if we hypothetically modify the student's workload, schedule, recovery, or study conditions?"

IMPORTANT: This system does NOT claim causal inference.
Use language such as: "model-estimated risk under the hypothetical scenario"
NOT: "this intervention causes a reduction in overload."

Core Components:
- PredictionService: Load trained Phase 4 model artifacts
- ScenarioSchema: Typed scenario representation
- StateModifier: Safe state cloning without baseline mutation
- FeatureRecalculator: Recompute 46 features after scenario modification
- CounterfactualEngine: Simulate baseline → counterfactual → delta
- ScenarioGenerator: Generate candidate scenarios from current state
- ScenarioRanker: Rank scenarios by risk/strain reduction + feasibility
- Validation: Sanity tests and experimental validation

All features recalculated using Phase 3 FeatureEngine (no manual modifications).
Temporal safety enforced: modifications only to future plan (day t+1 onward).
"""

from simulation.prediction_service import PredictionService
from simulation.scenario_schema import Scenario, ScenarioType
from simulation.state_modifier import StateModifier
from simulation.feature_recalculator import FeatureRecalculator
from simulation.counterfactual_engine import CounterfactualEngine, CounterfactualResult
from simulation.scenario_generator import ScenarioGenerator
from simulation.scenario_ranker import ScenarioRanker

__all__ = [
    'PredictionService',
    'Scenario',
    'ScenarioType',
    'StateModifier',
    'FeatureRecalculator',
    'CounterfactualEngine',
    'CounterfactualResult',
    'ScenarioGenerator',
    'ScenarioRanker',
]
