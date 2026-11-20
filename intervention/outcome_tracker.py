"""
KAIROS-TWIN Phase 6: Outcome Tracker.

Tracks intervention outcomes by:
1. Observing actual state changes at day+7
2. Re-computing risk predictions
3. Collecting student self-report feedback
4. Comparing predicted vs actual outcomes
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from pathlib import Path

from core.schemas import StudentTwinState
from core.twin_engine import TwinEngine
from simulation.prediction_service import PredictionService


@dataclass
class OutcomeReport:
    """
    Outcome report for a single intervention.

    Compares predicted vs actual impact after tracking period.
    """
    # Identifiers
    outcome_id: str
    intervention_id: str
    student_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Baseline (day 0 - when intervention was accepted)
    baseline_day: int = 0
    baseline_risk: float = 0.0
    baseline_strain: Optional[float] = None

    # Predicted impact (from CounterfactualEngine at day 0)
    predicted_risk_delta: float = 0.0
    predicted_strain_delta: Optional[float] = None
    predicted_counterfactual_risk: float = 0.0

    # Actual impact (measured at day+7)
    followup_day: int = 7
    actual_risk_at_day7: float = 0.0
    actual_risk_delta: float = 0.0
    actual_strain_at_day7: Optional[float] = None
    actual_strain_delta: Optional[float] = None

    # State changes (observed differences)
    state_changes: Dict[str, Any] = field(default_factory=dict)  # {field_name: {before, after, delta}}

    # Student self-report
    student_self_report: Optional[str] = None  # "helped", "no_change", "worse", "partial"
    student_feedback_text: Optional[str] = None

    # Success metrics
    was_successful: bool = False  # Did risk decrease?
    prediction_accuracy: Optional[float] = None  # |predicted_delta - actual_delta|
    confidence: float = 0.5  # [0, 1]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'outcome_id': self.outcome_id,
            'intervention_id': self.intervention_id,
            'student_id': self.student_id,
            'timestamp': self.timestamp,
            'baseline_day': self.baseline_day,
            'baseline_risk': self.baseline_risk,
            'baseline_strain': self.baseline_strain,
            'predicted_risk_delta': self.predicted_risk_delta,
            'predicted_strain_delta': self.predicted_strain_delta,
            'predicted_counterfactual_risk': self.predicted_counterfactual_risk,
            'followup_day': self.followup_day,
            'actual_risk_at_day7': self.actual_risk_at_day7,
            'actual_risk_delta': self.actual_risk_delta,
            'actual_strain_at_day7': self.actual_strain_at_day7,
            'actual_strain_delta': self.actual_strain_delta,
            'state_changes': self.state_changes,
            'student_self_report': self.student_self_report,
            'student_feedback_text': self.student_feedback_text,
            'was_successful': self.was_successful,
            'prediction_accuracy': self.prediction_accuracy,
            'confidence': self.confidence,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "OutcomeReport":
        """Reconstruct from dictionary."""
        return cls(**d)

    def format_summary(self) -> str:
        """Format human-readable summary."""
        lines = []
        lines.append(f"## Outcome Report")
        lines.append(f"**Student:** {self.student_id}")
        lines.append(f"**Period:** Day {self.baseline_day} → Day {self.followup_day}")
        lines.append("")

        lines.append("**Predicted Impact:**")
        lines.append(f"- Risk reduction: {abs(self.predicted_risk_delta):.1%}")
        lines.append(f"- Target risk: {self.predicted_counterfactual_risk:.1%}")
        lines.append("")

        lines.append("**Actual Impact:**")
        lines.append(f"- Risk change: {self.actual_risk_delta:+.1%} (from {self.baseline_risk:.1%} to {self.actual_risk_at_day7:.1%})")
        lines.append(f"- Success: {'Yes' if self.was_successful else 'No'}")
        if self.prediction_accuracy is not None:
            lines.append(f"- Prediction accuracy: {self.prediction_accuracy:.1%} error")
        lines.append("")

        if self.state_changes:
            lines.append("**Observed State Changes:**")
            for field, change in list(self.state_changes.items())[:5]:
                lines.append(f"- {field}: {change.get('before', 'N/A')} → {change.get('after', 'N/A')}")
            lines.append("")

        if self.student_self_report:
            lines.append(f"**Student Self-Report:** {self.student_self_report}")
            if self.student_feedback_text:
                lines.append(f"  \"{self.student_feedback_text}\"")

        return "\n".join(lines)


class OutcomeTracker:
    """
    Tracks intervention outcomes over time.

    For each accepted intervention:
    1. Log baseline state and prediction
    2. Wait 7 days (tracking period)
    3. Re-compute StudentTwinState at day+7
    4. Re-predict risk
    5. Compare actual vs predicted changes
    6. (Optional) Collect student self-report
    7. Generate OutcomeReport
    """

    def __init__(
        self,
        tracker_path: str = "data/phase6/outcome_tracker.json",
        twin_engine: Optional[TwinEngine] = None,
        prediction_service: Optional[PredictionService] = None,
    ):
        """
        Initialize outcome tracker.

        Args:
            tracker_path: Path to JSON file storing outcomes
            twin_engine: TwinEngine for recomputing state (if None, creates default)
            prediction_service: PredictionService for predictions (if None, loads default)
        """
        self.tracker_path = Path(tracker_path)
        self.reports: Dict[str, OutcomeReport] = {}

        # Phase 3 and Phase 5 tools
        self.twin_engine = twin_engine or TwinEngine()
        self.prediction_service = prediction_service or PredictionService()

        self._load()

    def _load(self) -> None:
        """Load existing outcomes from disk."""
        if self.tracker_path.exists():
            try:
                with open(self.tracker_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for outcome_id, outcome_dict in data.items():
                        self.reports[outcome_id] = OutcomeReport.from_dict(outcome_dict)
                print(f"[OutcomeTracker] Loaded {len(self.reports)} reports from {self.tracker_path}")
            except Exception as e:
                print(f"Warning: Could not load outcome tracker: {e}")
        else:
            # Create directory if needed
            self.tracker_path.parent.mkdir(parents=True, exist_ok=True)

    def _save(self) -> None:
        """Save outcomes to disk."""
        try:
            with open(self.tracker_path, 'w', encoding='utf-8') as f:
                data = {
                    outcome_id: report.to_dict()
                    for outcome_id, report in self.reports.items()
                }
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save outcome tracker: {e}")

    def start_tracking(
        self,
        intervention_id: str,
        student_id: str,
        baseline_state: Optional[StudentTwinState],
        baseline_risk: float,
        baseline_strain: Optional[float],
        predicted_risk_delta: float,
        predicted_counterfactual_risk: float,
        predicted_strain_delta: Optional[float] = None,
    ) -> str:
        """
        Start tracking an accepted intervention.

        Args:
            intervention_id: Intervention identifier
            student_id: Student identifier
            baseline_state: State when intervention was accepted (can be None)
            baseline_risk: Baseline overload risk
            baseline_strain: Baseline strain index
            predicted_risk_delta: Predicted risk change from CounterfactualEngine
            predicted_counterfactual_risk: Predicted risk under scenario
            predicted_strain_delta: Predicted strain change

        Returns:
            Outcome ID
        """
        outcome_id = f"outcome_{intervention_id}"

        # Use provided baseline_state day, or default to 0
        baseline_day = baseline_state.day if baseline_state is not None else 0

        report = OutcomeReport(
            outcome_id=outcome_id,
            intervention_id=intervention_id,
            student_id=student_id,
            baseline_day=baseline_day,
            baseline_risk=baseline_risk,
            baseline_strain=baseline_strain,
            predicted_risk_delta=predicted_risk_delta,
            predicted_counterfactual_risk=predicted_counterfactual_risk,
            predicted_strain_delta=predicted_strain_delta,
        )

        self.reports[outcome_id] = report
        self._save()

        return outcome_id

    def record_followup(
        self,
        outcome_id: str,
        followup_state: StudentTwinState,
        followup_day: int,
    ) -> OutcomeReport:
        """
        Record followup state at day+7 and compute actual outcomes.

        Args:
            outcome_id: Outcome identifier
            followup_state: StudentTwinState at day+7
            followup_day: Day of followup (typically baseline_day + 7)

        Returns:
            Updated OutcomeReport
        """
        if outcome_id not in self.reports:
            raise ValueError(f"Outcome {outcome_id} not found")

        report = self.reports[outcome_id]

        # Re-predict risk at day+7
        followup_snapshot = self.prediction_service.predict(followup_state, followup_day)
        actual_risk = followup_snapshot.overload_probability
        actual_strain = followup_snapshot.strain_index

        # Calculate actual deltas
        report.followup_day = followup_day
        report.actual_risk_at_day7 = actual_risk
        report.actual_risk_delta = report.baseline_risk - actual_risk  # Positive = improvement

        if actual_strain is not None and report.baseline_strain is not None:
            report.actual_strain_at_day7 = actual_strain
            report.actual_strain_delta = report.baseline_strain - actual_strain

        # Calculate success
        report.was_successful = report.actual_risk_delta > 0  # Risk decreased

        # Calculate prediction accuracy (error)
        report.prediction_accuracy = abs(report.predicted_risk_delta - report.actual_risk_delta)

        # Calculate confidence based on accuracy
        if report.prediction_accuracy <= 0.05:
            report.confidence = 0.95
        elif report.prediction_accuracy <= 0.10:
            report.confidence = 0.80
        elif report.prediction_accuracy <= 0.15:
            report.confidence = 0.60
        else:
            report.confidence = 0.40

        # TODO: Compare state changes (sleep, study hours, stress, etc.)
        # For now, we'll leave state_changes empty

        self._save()

        return report

    def add_student_feedback(
        self,
        outcome_id: str,
        self_report: str,
        feedback_text: Optional[str] = None,
    ) -> None:
        """
        Add student self-report feedback.

        Args:
            outcome_id: Outcome identifier
            self_report: "helped", "no_change", "worse", "partial"
            feedback_text: Optional free-form feedback
        """
        if outcome_id not in self.reports:
            raise ValueError(f"Outcome {outcome_id} not found")

        report = self.reports[outcome_id]
        report.student_self_report = self_report
        report.student_feedback_text = feedback_text

        self._save()

    def get_report(self, outcome_id: str) -> Optional[OutcomeReport]:
        """Get a specific outcome report."""
        return self.reports.get(outcome_id)

    def get_student_outcomes(self, student_id: str) -> List[OutcomeReport]:
        """Get all outcome reports for a student."""
        return [
            report for report in self.reports.values()
            if report.student_id == student_id
        ]

    def get_success_rate(self, student_id: Optional[str] = None) -> float:
        """
        Calculate success rate (percentage where risk decreased).

        Args:
            student_id: If provided, calculate for single student; otherwise global

        Returns:
            Success rate [0, 1]
        """
        reports = self.reports.values()
        if student_id:
            reports = [r for r in reports if r.student_id == student_id]

        completed = [r for r in reports if r.actual_risk_at_day7 is not None]
        successful = [r for r in completed if r.was_successful]

        return len(successful) / len(completed) if len(completed) > 0 else 0.0

    def get_prediction_accuracy_stats(self) -> Dict[str, float]:
        """
        Calculate prediction accuracy statistics.

        Returns:
            Stats dict with mean_error, median_error, etc.
        """
        completed = [
            r for r in self.reports.values()
            if r.prediction_accuracy is not None
        ]

        if not completed:
            return {'n': 0}

        errors = [r.prediction_accuracy for r in completed]
        errors.sort()

        return {
            'n': len(errors),
            'mean_error': sum(errors) / len(errors),
            'median_error': errors[len(errors) // 2],
            'min_error': min(errors),
            'max_error': max(errors),
        }
