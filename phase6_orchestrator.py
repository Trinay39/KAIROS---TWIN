"""
KAIROS-TWIN Phase 6: Main Orchestrator Entry Point.

This is the main interface for Phase 6 intervention system:
  StudentTwinState → Diagnosis → Scenarios → Ranking → Recommendation

Usage:
    from phase6_orchestrator import Phase6System

    system = Phase6System()
    recommendation = system.recommend_intervention(twin_state, day)
    print(recommendation.format_for_student())
"""
from __future__ import annotations
from typing import Optional, Dict, Any
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.schemas import StudentTwinState
from core.twin_engine import TwinEngine
from simulation.prediction_service import PredictionService

from agents.orchestrator_agent import OrchestratorAgent
from agents.llm_reasoner import LLMReasoner
from intervention.recommendation import Recommendation, RecommendationConfig
from intervention.intervention_registry import InterventionRegistry
from intervention.outcome_tracker import OutcomeTracker


class Phase6System:
    """
    Main entry point for Phase 6 Multi-Agent Intervention System.

    This class provides a simple interface for:
    1. Generating intervention recommendations
    2. Logging student responses
    3. Tracking outcomes

    Example:
        system = Phase6System()

        # Get recommendation
        recommendation = system.recommend_intervention(twin_state, day=50)
        print(recommendation.format_for_student())

        # Log student acceptance
        intervention_id = system.log_intervention(recommendation, "accepted")

        # Track outcome at day+7
        system.track_outcome(intervention_id, followup_state, day=57)
    """

    def __init__(
        self,
        llm_api_key: Optional[str] = None,
        config: Optional[RecommendationConfig] = None,
        registry_path: str = "data/phase6/intervention_registry.json",
        tracker_path: str = "data/phase6/outcome_tracker.json",
    ):
        """
        Initialize Phase 6 system.

        Args:
            llm_api_key: Anthropic API key (if None, uses mock LLM)
            config: Recommendation configuration
            registry_path: Path to intervention registry
            tracker_path: Path to outcome tracker
        """
        # Configuration
        self.config = config or RecommendationConfig()

        # Phase 3 and Phase 5 tools
        self.twin_engine = TwinEngine()
        self.prediction_service = PredictionService()

        # Phase 6 components
        self.llm_reasoner = LLMReasoner(api_key=llm_api_key)
        self.orchestrator = OrchestratorAgent(
            llm_reasoner=self.llm_reasoner,
            prediction_service=self.prediction_service,
            config=self.config,
        )

        # Tracking systems
        self.registry = InterventionRegistry(registry_path=registry_path)
        self.outcome_tracker = OutcomeTracker(
            tracker_path=tracker_path,
            twin_engine=self.twin_engine,
            prediction_service=self.prediction_service,
        )

        print("[Phase6System] Initialized successfully")
        if llm_api_key is None:
            print("  [Warning] No LLM API key provided - using mock responses")

    def recommend_intervention(
        self,
        twin_state: StudentTwinState,
        day: Optional[int] = None,
    ) -> Recommendation:
        """
        Generate intervention recommendation for a student.

        Args:
            twin_state: StudentTwinState at time t
            day: Current semester day (if None, uses twin_state.day)

        Returns:
            Recommendation object
        """
        if day is None:
            day = twin_state.day

        print(f"[Phase6System] Generating recommendation for {twin_state.student_id} at day {day}")

        # Run orchestration
        recommendation = self.orchestrator.orchestrate(twin_state, day, parallel_agents=True)

        print(f"  [Recommended] {recommendation.scenario_type}: {recommendation.scenario_description}")
        print(f"  [Estimated impact] Risk: {recommendation.baseline_risk:.1%} → {recommendation.counterfactual_risk:.1%} (Δ {recommendation.risk_delta:+.1%})")

        return recommendation

    def log_intervention(
        self,
        recommendation: Recommendation,
        student_response: Optional[str] = None,
        feedback: Optional[str] = None,
    ) -> str:
        """
        Log an intervention in the registry.

        Args:
            recommendation: Recommendation that was presented
            student_response: "accepted", "rejected", "deferred", "ask_more", or None
            feedback: Optional student feedback text

        Returns:
            Intervention ID
        """
        student_id = recommendation.student_id
        day = recommendation.day

        # Log intervention
        intervention_id = self.registry.log_intervention(
            student_id=student_id,
            recommendation=recommendation,
            day=day,
        )

        print(f"[Phase6System] Logged intervention {intervention_id}")

        # Update with student response if provided
        if student_response:
            self.registry.update_student_response(
                intervention_id=intervention_id,
                response=student_response,
                day=day,
                feedback=feedback,
            )
            print(f"  [Student response] {student_response}")

            # If accepted, start outcome tracking
            if student_response == "accepted":
                self._start_outcome_tracking(
                    intervention_id=intervention_id,
                    recommendation=recommendation,
                )

        return intervention_id

    def _start_outcome_tracking(
        self,
        intervention_id: str,
        recommendation: Recommendation,
    ) -> str:
        """
        Start tracking outcome for an accepted intervention.

        Args:
            intervention_id: Intervention identifier
            recommendation: The recommendation that was accepted

        Returns:
            Outcome ID
        """
        outcome_id = self.outcome_tracker.start_tracking(
            intervention_id=intervention_id,
            student_id=recommendation.student_id,
            baseline_state=None,  # Would need to pass this separately
            baseline_risk=recommendation.baseline_risk,
            baseline_strain=recommendation.strain_delta,
            predicted_risk_delta=recommendation.risk_delta,
            predicted_counterfactual_risk=recommendation.counterfactual_risk,
            predicted_strain_delta=recommendation.strain_delta,
        )

        print(f"  [Outcome tracking] Started {outcome_id}")
        return outcome_id

    def track_outcome(
        self,
        intervention_id: str,
        followup_state: StudentTwinState,
        followup_day: int,
        student_feedback: Optional[str] = None,
        student_feedback_text: Optional[str] = None,
    ) -> str:
        """
        Track outcome at followup (typically day+7).

        Args:
            intervention_id: Intervention identifier
            followup_state: StudentTwinState at followup day
            followup_day: Day of followup
            student_feedback: "helped", "no_change", "worse", "partial"
            student_feedback_text: Optional free-form feedback

        Returns:
            Outcome ID
        """
        outcome_id = f"outcome_{intervention_id}"

        print(f"[Phase6System] Tracking outcome for {intervention_id} at day {followup_day}")

        # Record followup
        report = self.outcome_tracker.record_followup(
            outcome_id=outcome_id,
            followup_state=followup_state,
            followup_day=followup_day,
        )

        print(f"  [Outcome] Risk: {report.baseline_risk:.1%} → {report.actual_risk_at_day7:.1%} (Δ {report.actual_risk_delta:+.1%})")
        print(f"  [Success] {report.was_successful}")
        print(f"  [Accuracy] {report.prediction_accuracy:.1%} error")

        # Add student feedback if provided
        if student_feedback:
            self.outcome_tracker.add_student_feedback(
                outcome_id=outcome_id,
                self_report=student_feedback,
                feedback_text=student_feedback_text,
            )
            print(f"  [Student feedback] {student_feedback}")

        # Update registry with outcome
        self.registry.update_outcome(
            intervention_id=intervention_id,
            actual_risk_at_day7=report.actual_risk_at_day7,
            outcome_report_id=outcome_id,
        )

        return outcome_id

    def get_student_history(self, student_id: str) -> Dict[str, Any]:
        """
        Get complete intervention history for a student.

        Args:
            student_id: Student identifier

        Returns:
            History dict with interventions, outcomes, stats
        """
        interventions = self.registry.get_student_history(student_id)
        outcomes = self.outcome_tracker.get_student_outcomes(student_id)

        return {
            'student_id': student_id,
            'total_interventions': len(interventions),
            'acceptance_rate': self.registry.get_acceptance_rate(student_id),
            'completion_rate': self.registry.get_completion_rate(student_id),
            'success_rate': self.outcome_tracker.get_success_rate(student_id),
            'interventions': [i.to_dict() for i in interventions],
            'outcomes': [o.to_dict() for o in outcomes],
        }

    def get_system_statistics(self) -> Dict[str, Any]:
        """
        Get global system statistics.

        Returns:
            Statistics dict
        """
        return {
            'registry': {
                'total_interventions': len(self.registry.records),
                'acceptance_rate': self.registry.get_acceptance_rate(),
                'completion_rate': self.registry.get_completion_rate(),
                'effectiveness': self.registry.get_effectiveness_stats(),
                'by_scenario_type': self.registry.get_scenario_type_stats(),
            },
            'outcomes': {
                'total_tracked': len(self.outcome_tracker.reports),
                'success_rate': self.outcome_tracker.get_success_rate(),
                'prediction_accuracy': self.outcome_tracker.get_prediction_accuracy_stats(),
            },
            'supported_scenarios': self.orchestrator.list_supported_scenarios(),
        }

    def validate_safety(self, twin_state: StudentTwinState, day: int = 0) -> bool:
        """
        Validate that system respects all safety constraints.

        Args:
            twin_state: Sample state to test
            day: Day to test

        Returns:
            True if all safety checks pass
        """
        print("[Phase6System] Running safety validation...")

        is_safe, violations = self.orchestrator.validate_safety_constraints(twin_state, day)

        if is_safe:
            print("  [✓] All safety checks passed")
        else:
            print("  [✗] Safety violations detected:")
            for violation in violations:
                print(f"    - {violation}")

        return is_safe


def demo():
    """
    Demo the Phase 6 system with a sample student.
    """
    print("="*80)
    print("KAIROS-TWIN Phase 6: Multi-Agent Intervention System Demo")
    print("="*80)
    print()

    # Initialize system
    system = Phase6System()

    # Load a sample state (you would normally get this from TwinEngine)
    from core.schemas import (
        StudentTwinState, AcademicState, BehavioralState,
        RecoveryState, WorkloadState, EngagementState,
        TemporalContext, PredictionSnapshot, HistorySummary
    )

    # Create sample high-risk student
    sample_state = StudentTwinState(
        student_id="DEMO_001",
        day=50,
        academic=AcademicState(
            attendance_rate_7d=0.75,
            grade_trend_30d=-0.04,
            missed_deadlines_14d=3,
            academic_load_score=0.85,
        ),
        behavioral=BehavioralState(
            avg_study_hours_7d=2.5,
            study_consistency_score=0.4,
            procrastination_index_7d=0.7,
        ),
        recovery=RecoveryState(
            avg_sleep_hours_7d=5.5,
            sleep_deficit_7d_hours=12.0,
            recovery_score_7d=0.3,
        ),
        workload=WorkloadState(
            pending_assignment_count=12,
            deadline_density_next_7_known=5,
            workload_pressure_score_7d=0.88,
        ),
        engagement=EngagementState(
            avg_stress_7d=0.85,
            avg_confidence_7d=2.0,
        ),
        temporal=TemporalContext(day_of_semester=50),
        predictions=PredictionSnapshot(),
        history=HistorySummary(),
    )

    # Get recommendation
    print("\n" + "="*80)
    print("STEP 1: Generate Recommendation")
    print("="*80)
    recommendation = system.recommend_intervention(sample_state, day=50)

    print("\n" + "-"*80)
    print("RECOMMENDATION FOR STUDENT:")
    print("-"*80)
    print(recommendation.format_for_student())

    # Log intervention
    print("\n" + "="*80)
    print("STEP 2: Log Student Response")
    print("="*80)
    intervention_id = system.log_intervention(
        recommendation=recommendation,
        student_response="accepted",
        feedback="I'll try this approach",
    )

    # Get statistics
    print("\n" + "="*80)
    print("STEP 3: System Statistics")
    print("="*80)
    stats = system.get_system_statistics()
    print(f"Total interventions: {stats['registry']['total_interventions']}")
    print(f"Acceptance rate: {stats['registry']['acceptance_rate']:.1%}")

    print("\n" + "="*80)
    print("Demo complete!")
    print("="*80)


if __name__ == '__main__':
    demo()
