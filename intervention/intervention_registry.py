"""
KAIROS-TWIN Phase 6: Intervention Registry.

Logs all interventions offered, accepted, rejected, and their outcomes.
Provides history and analytics for intervention effectiveness.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import json
from pathlib import Path


class InterventionStatus(Enum):
    """Status of an intervention."""
    OFFERED = "offered"      # Presented to student
    ACCEPTED = "accepted"    # Student accepted
    REJECTED = "rejected"    # Student rejected
    DEFERRED = "deferred"    # Student postponed decision
    COMPLETED = "completed"  # Student reported completion
    EXPIRED = "expired"      # Tracking period ended


@dataclass
class InterventionRecord:
    """
    Single intervention record.

    Tracks:
    - When offered, accepted, completed
    - Student response
    - Baseline and counterfactual states
    - Actual outcomes (if tracked)
    """
    # Identifiers
    intervention_id: str
    student_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Recommendation details
    scenario_id: str = ""
    scenario_type: str = ""
    scenario_description: str = ""

    # Predicted impact (from CounterfactualEngine)
    baseline_risk: float = 0.0
    counterfactual_risk: float = 0.0
    predicted_risk_delta: float = 0.0
    predicted_strain_delta: Optional[float] = None

    # Status tracking
    status: InterventionStatus = InterventionStatus.OFFERED
    offered_at_day: int = 0
    accepted_at_day: Optional[int] = None
    completed_at_day: Optional[int] = None

    # Student response
    student_response: Optional[str] = None  # "accepted", "rejected", "deferred", "ask_more"
    student_feedback: Optional[str] = None  # Free-form feedback

    # Actual outcomes (tracked by OutcomeTracker)
    actual_risk_at_day7: Optional[float] = None
    actual_risk_delta: Optional[float] = None
    outcome_report_id: Optional[str] = None

    # Metadata
    agent_diagnoses: List[str] = field(default_factory=list)  # Which agents flagged issues
    recommendation_confidence: str = "medium"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'intervention_id': self.intervention_id,
            'student_id': self.student_id,
            'timestamp': self.timestamp,
            'scenario_id': self.scenario_id,
            'scenario_type': self.scenario_type,
            'scenario_description': self.scenario_description,
            'baseline_risk': self.baseline_risk,
            'counterfactual_risk': self.counterfactual_risk,
            'predicted_risk_delta': self.predicted_risk_delta,
            'predicted_strain_delta': self.predicted_strain_delta,
            'status': self.status.value,
            'offered_at_day': self.offered_at_day,
            'accepted_at_day': self.accepted_at_day,
            'completed_at_day': self.completed_at_day,
            'student_response': self.student_response,
            'student_feedback': self.student_feedback,
            'actual_risk_at_day7': self.actual_risk_at_day7,
            'actual_risk_delta': self.actual_risk_delta,
            'outcome_report_id': self.outcome_report_id,
            'agent_diagnoses': self.agent_diagnoses,
            'recommendation_confidence': self.recommendation_confidence,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "InterventionRecord":
        """Reconstruct from dictionary."""
        # Convert status string to enum
        if 'status' in d and isinstance(d['status'], str):
            d['status'] = InterventionStatus(d['status'])
        return cls(**d)


class InterventionRegistry:
    """
    Registry of all interventions.

    Maintains persistent log of:
    - All interventions offered to students
    - Student acceptance/rejection decisions
    - Outcome tracking results

    Stored in JSON format for simplicity (can migrate to DB later).
    """

    def __init__(self, registry_path: str = "data/phase6/intervention_registry.json"):
        """
        Initialize registry.

        Args:
            registry_path: Path to JSON file storing interventions
        """
        self.registry_path = Path(registry_path)
        self.records: Dict[str, InterventionRecord] = {}
        self._load()

    def _load(self) -> None:
        """Load existing registry from disk."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for record_id, record_dict in data.items():
                        self.records[record_id] = InterventionRecord.from_dict(record_dict)
                print(f"[InterventionRegistry] Loaded {len(self.records)} records from {self.registry_path}")
            except Exception as e:
                print(f"Warning: Could not load registry: {e}")
        else:
            # Create directory if needed
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)

    def _save(self) -> None:
        """Save registry to disk."""
        try:
            with open(self.registry_path, 'w', encoding='utf-8') as f:
                data = {
                    record_id: record.to_dict()
                    for record_id, record in self.records.items()
                }
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save registry: {e}")

    def log_intervention(
        self,
        student_id: str,
        recommendation,  # Recommendation object
        day: int,
    ) -> str:
        """
        Log a new intervention offered to student.

        Args:
            student_id: Student identifier
            recommendation: Recommendation object from OrchestratorAgent
            day: Semester day when offered

        Returns:
            Intervention ID
        """
        intervention_id = f"{student_id}_{day}_{datetime.now().timestamp()}"

        record = InterventionRecord(
            intervention_id=intervention_id,
            student_id=student_id,
            scenario_id=recommendation.scenario_id,
            scenario_type=recommendation.scenario_type,
            scenario_description=recommendation.scenario_description,
            baseline_risk=recommendation.baseline_risk,
            counterfactual_risk=recommendation.counterfactual_risk,
            predicted_risk_delta=recommendation.risk_delta,
            predicted_strain_delta=recommendation.strain_delta,
            status=InterventionStatus.OFFERED,
            offered_at_day=day,
            agent_diagnoses=recommendation.primary_diagnoses,
            recommendation_confidence=recommendation.confidence.value,
        )

        self.records[intervention_id] = record
        self._save()

        return intervention_id

    def update_student_response(
        self,
        intervention_id: str,
        response: str,
        day: int,
        feedback: Optional[str] = None,
    ) -> None:
        """
        Update intervention with student response.

        Args:
            intervention_id: Intervention identifier
            response: "accepted", "rejected", "deferred", "ask_more"
            day: Day of response
            feedback: Optional student feedback text
        """
        if intervention_id not in self.records:
            raise ValueError(f"Intervention {intervention_id} not found")

        record = self.records[intervention_id]
        record.student_response = response
        record.student_feedback = feedback

        # Update status
        if response == "accepted":
            record.status = InterventionStatus.ACCEPTED
            record.accepted_at_day = day
        elif response == "rejected":
            record.status = InterventionStatus.REJECTED
        elif response == "deferred":
            record.status = InterventionStatus.DEFERRED

        self._save()

    def update_outcome(
        self,
        intervention_id: str,
        actual_risk_at_day7: float,
        outcome_report_id: Optional[str] = None,
    ) -> None:
        """
        Update intervention with actual outcome.

        Args:
            intervention_id: Intervention identifier
            actual_risk_at_day7: Actual risk measured at day+7
            outcome_report_id: Optional link to detailed OutcomeReport
        """
        if intervention_id not in self.records:
            raise ValueError(f"Intervention {intervention_id} not found")

        record = self.records[intervention_id]
        record.actual_risk_at_day7 = actual_risk_at_day7
        record.actual_risk_delta = record.baseline_risk - actual_risk_at_day7
        record.outcome_report_id = outcome_report_id
        record.status = InterventionStatus.COMPLETED

        self._save()

    def get_student_history(self, student_id: str) -> List[InterventionRecord]:
        """Get all interventions for a student."""
        return [
            record for record in self.records.values()
            if record.student_id == student_id
        ]

    def get_acceptance_rate(self, student_id: Optional[str] = None) -> float:
        """
        Calculate intervention acceptance rate.

        Args:
            student_id: If provided, calculate for single student; otherwise global

        Returns:
            Acceptance rate [0, 1]
        """
        records = self.records.values()
        if student_id:
            records = [r for r in records if r.student_id == student_id]

        offered = len(records)
        accepted = len([r for r in records if r.status == InterventionStatus.ACCEPTED])

        return accepted / offered if offered > 0 else 0.0

    def get_completion_rate(self, student_id: Optional[str] = None) -> float:
        """
        Calculate intervention completion rate.

        Args:
            student_id: If provided, calculate for single student; otherwise global

        Returns:
            Completion rate [0, 1]
        """
        records = self.records.values()
        if student_id:
            records = [r for r in records if r.student_id == student_id]

        accepted = [r for r in records if r.status == InterventionStatus.ACCEPTED]
        completed = [r for r in records if r.status == InterventionStatus.COMPLETED]

        return len(completed) / len(accepted) if len(accepted) > 0 else 0.0

    def get_effectiveness_stats(self) -> Dict[str, Any]:
        """
        Calculate effectiveness statistics across all interventions.

        Returns:
            Statistics dict
        """
        completed = [
            r for r in self.records.values()
            if r.status == InterventionStatus.COMPLETED and r.actual_risk_delta is not None
        ]

        if not completed:
            return {'n': 0, 'msg': 'No completed interventions'}

        predicted_deltas = [r.predicted_risk_delta for r in completed]
        actual_deltas = [r.actual_risk_delta for r in completed]

        return {
            'n': len(completed),
            'predicted_mean_delta': sum(predicted_deltas) / len(predicted_deltas),
            'actual_mean_delta': sum(actual_deltas) / len(actual_deltas),
            'accuracy': sum(1 for i in range(len(completed)) if abs(predicted_deltas[i] - actual_deltas[i]) < 0.1) / len(completed),
            'successful': sum(1 for d in actual_deltas if d > 0) / len(actual_deltas),
        }

    def get_scenario_type_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics by scenario type.

        Returns:
            Dict mapping scenario_type -> stats
        """
        from collections import defaultdict

        stats = defaultdict(lambda: {'offered': 0, 'accepted': 0, 'completed': 0})

        for record in self.records.values():
            scenario_type = record.scenario_type
            stats[scenario_type]['offered'] += 1
            if record.status in [InterventionStatus.ACCEPTED, InterventionStatus.COMPLETED]:
                stats[scenario_type]['accepted'] += 1
            if record.status == InterventionStatus.COMPLETED:
                stats[scenario_type]['completed'] += 1

        return dict(stats)
