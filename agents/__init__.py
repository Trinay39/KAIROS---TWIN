"""
KAIROS-TWIN Phase 6: Multi-Agent Intervention System.

This package provides specialized agents that diagnose student problems
and recommend interventions using Phase 5 tools (PredictionService,
CounterfactualEngine, ScenarioGenerator, ScenarioRanker).

All agents use deterministic Phase 5 tools and avoid:
- Inventing or modifying probability values
- Making causal claims (use "model estimates" instead of "causes")
- Retraining or modifying Phase 4 models
"""

from agents.base_agent import BaseAgent, AgentDiagnosis
from agents.academic_agent import AcademicAgent
from agents.behavioral_agent import BehavioralAgent
from agents.recovery_agent import RecoveryAgent
from agents.workload_agent import WorkloadAgent
from agents.schedule_agent import ScheduleAgent
from agents.orchestrator_agent import OrchestratorAgent
from agents.llm_reasoner import LLMReasoner, Recommendation, RecommendationConfig

__all__ = [
    # Base classes
    'BaseAgent',
    'AgentDiagnosis',
    'Recommendation',
    'RecommendationConfig',
    # Specialized agents
    'AcademicAgent',
    'BehavioralAgent',
    'RecoveryAgent',
    'WorkloadAgent',
    'ScheduleAgent',
    'OrchestratorAgent',
    # LLM integration
    'LLMReasoner',
]
