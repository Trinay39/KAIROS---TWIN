"""
KAIROS-TWIN Phase 6: Base Agent Class.

Abstract base class for all specialized agents in the multi-agent system.
Each agent reads a specific dimension of the StudentTwinState and produces
a diagnosis of problems with severity scores and suggested scenarios.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum


class Severity(Enum):
    """Diagnosis severity levels."""
    LOW = "low"        # Minor issue, monitoring recommended
    MEDIUM = "medium"  # Noticeable issue, intervention suggested
    HIGH = "high"      # Significant issue, intervention recommended
    CRITICAL = "critical"  # Urgent issue, immediate intervention needed


@dataclass
class AgentDiagnosis:
    """
    Output from a specialized agent.

    Contains:
    - issue_name: Short identifier for the problem
    - severity: How serious the issue is
    - description: Human-readable explanation
    - affected_fields: Which state fields are involved
    - suggested_scenario_types: Which Phase 5 scenarios might help
    - confidence: Agent's confidence in this diagnosis [0, 1]
    """
    issue_name: str
    severity: Severity
    description: str
    affected_fields: List[str]
    suggested_scenario_types: List[str]
    confidence: float = 1.0


class BaseAgent(ABC):
    """
    Abstract base class for all specialized agents.

    Each agent:
    1. Reads a specific layer of StudentTwinState
    2. Identifies problematic patterns
    3. Rates severity and confidence
    4. Suggests Phase 5 scenarios that might help

    All agents must implement:
    - diagnose(): Main diagnostic method
    - get_supported_scenarios(): Which scenarios this agent handles
    """

    def __init__(self, name: str, description: str):
        """
        Initialize an agent.

        Args:
            name: Agent identifier (e.g., "AcademicAgent")
            description: What this agent analyzes
        """
        self.name = name
        self.description = description

    @abstractmethod
    def diagnose(self, state_layer: Any, day: int = 0) -> List[AgentDiagnosis]:
        """
        Analyze the state layer and return diagnoses.

        Args:
            state_layer: The specific state layer this agent handles
                         (e.g., AcademicState, BehavioralState)
            day: Current semester day for context

        Returns:
            List of AgentDiagnosis objects (empty if no issues found)
        """
        pass

    @abstractmethod
    def get_supported_scenarios(self) -> List[str]:
        """
        Return list of scenario types this agent can trigger.

        Example: ["REDUCE_WORKLOAD", "REMOVE_ASSIGNMENT"]
        """
        pass

    def _classify_severity(self, metric_value: float, thresholds: Dict[str, float]) -> Severity:
        """
        Helper to classify severity based on thresholds.

        Args:
            metric_value: The measured value
            thresholds: Dict with keys "low", "medium", "high" specifying
                        the minimum value for each severity level

        Returns:
            Severity level
        """
        if metric_value >= thresholds.get("critical", float('inf')):
            return Severity.CRITICAL
        elif metric_value >= thresholds.get("high", float('inf')):
            return Severity.HIGH
        elif metric_value >= thresholds.get("medium", float('inf')):
            return Severity.MEDIUM
        elif metric_value >= thresholds.get("low", float('inf')):
            return Severity.LOW
        return Severity.LOW

    def _build_diagnosis(
        self,
        issue_name: str,
        severity: Severity,
        description: str,
        affected_fields: List[str],
        suggested_scenario_types: List[str],
        confidence: float = 1.0,
    ) -> AgentDiagnosis:
        """
        Helper to create a diagnosis with type safety.

        Args:
            issue_name: Short identifier
            severity: Severity level
            description: Human-readable explanation
            affected_fields: State fields involved
            suggested_scenario_types: Which Phase 5 scenarios might help
            confidence: Agent confidence [0, 1]

        Returns:
            AgentDiagnosis object
        """
        return AgentDiagnosis(
            issue_name=issue_name,
            severity=severity,
            description=description,
            affected_fields=affected_fields,
            suggested_scenario_types=suggested_scenario_types,
            confidence=confidence,
        )
