"""
KAIROS-TWIN Phase 6: Comprehensive Test Suite.

Tests for:
- Individual agent behavior (academic, behavioral, recovery, workload)
- End-to-end orchestration
- LLM safety validation
- Recommendation formatting
- Outcome tracking
"""
import pytest
from datetime import datetime
from types import SimpleNamespace

from core.schemas import (
    StudentTwinState, AcademicState, BehavioralState,
    RecoveryState, WorkloadState, EngagementState,
    TemporalContext, PredictionSnapshot, HistorySummary
)

from agents.base_agent import Severity
from agents.academic_agent import AcademicAgent
from agents.behavioral_agent import BehavioralAgent
from agents.recovery_agent import RecoveryAgent
from agents.workload_agent import WorkloadAgent
from agents.schedule_agent import ScheduleAgent
from agents.orchestrator_agent import OrchestratorAgent
from agents.llm_reasoner import LLMReasoner
from simulation.scenario_schema import ScenarioType

from intervention.recommendation import Recommendation, RecommendationConfig, RecommendationConfidence
from intervention.intervention_registry import InterventionRegistry, InterventionStatus
from intervention.outcome_tracker import OutcomeTracker, OutcomeReport

from phase6_orchestrator import Phase6System


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_low_risk_state():
    """Create a low-risk student state."""
    return StudentTwinState(
        student_id="LOW_RISK_001",
        day=50,
        academic=AcademicState(
            attendance_rate_7d=0.95,
            grade_trend_30d=0.02,
            missed_deadlines_14d=0,
            academic_load_score=0.4,
        ),
        behavioral=BehavioralState(
            avg_study_hours_7d=4.5,
            study_consistency_score=0.85,
            procrastination_index_7d=0.2,
        ),
        recovery=RecoveryState(
            avg_sleep_hours_7d=7.5,
            sleep_deficit_7d_hours=0.0,
            recovery_score_7d=0.9,
        ),
        workload=WorkloadState(
            pending_assignment_count=2,
            deadline_density_next_7_known=1,
            workload_pressure_score_7d=0.2,
        ),
        engagement=EngagementState(
            avg_stress_7d=0.3,
            avg_confidence_7d=4.5,
        ),
        temporal=TemporalContext(day_of_semester=50),
        predictions=PredictionSnapshot(),
        history=HistorySummary(),
    )


@pytest.fixture
def sample_high_risk_state():
    """Create a high-risk student state."""
    return StudentTwinState(
        student_id="HIGH_RISK_001",
        day=50,
        academic=AcademicState(
            attendance_rate_7d=0.70,
            grade_trend_30d=-0.05,
            missed_deadlines_14d=4,
            academic_load_score=0.90,
        ),
        behavioral=BehavioralState(
            avg_study_hours_7d=2.0,
            study_consistency_score=0.35,
            procrastination_index_7d=0.85,
        ),
        recovery=RecoveryState(
            avg_sleep_hours_7d=5.2,
            sleep_deficit_7d_hours=15.0,
            recovery_score_7d=0.25,
        ),
        workload=WorkloadState(
            pending_assignment_count=14,
            deadline_density_next_7_known=7,
            workload_pressure_score_7d=0.95,
        ),
        engagement=EngagementState(
            avg_stress_7d=0.90,
            avg_confidence_7d=1.5,
        ),
        temporal=TemporalContext(day_of_semester=50),
        predictions=PredictionSnapshot(),
        history=HistorySummary(),
    )


# ============================================================================
# Test Agent: Academic
# ============================================================================

class TestAcademicAgent:
    """Tests for AcademicAgent."""

    def test_diagnose_no_issues(self, sample_low_risk_state):
        """Test that low-risk state produces no issues."""
        agent = AcademicAgent()
        diagnoses = agent.diagnose(sample_low_risk_state.academic, day=50)
        assert len(diagnoses) == 0

    def test_diagnose_grade_deterioration(self, sample_high_risk_state):
        """Test detection of grade deterioration."""
        agent = AcademicAgent()
        diagnoses = agent.diagnose(sample_high_risk_state.academic, day=50)

        issue_names = [d.issue_name for d in diagnoses]
        assert "grade_deterioration" in issue_names

    def test_diagnose_missed_deadlines(self, sample_high_risk_state):
        """Test detection of missed deadlines."""
        agent = AcademicAgent()
        diagnoses = agent.diagnose(sample_high_risk_state.academic, day=50)

        issue_names = [d.issue_name for d in diagnoses]
        assert "missed_deadlines" in issue_names

    def test_supported_scenarios(self):
        """Test supported scenarios."""
        agent = AcademicAgent()
        scenarios = agent.get_supported_scenarios()

        assert "REDUCE_WORKLOAD" in scenarios
        assert "MOVE_ASSIGNMENT" in scenarios

    def test_diagnosis_severity(self, sample_high_risk_state):
        """Test that diagnoses have appropriate severity."""
        agent = AcademicAgent()
        diagnoses = agent.diagnose(sample_high_risk_state.academic, day=50)

        # Should have at least one high/critical severity
        severities = [d.severity for d in diagnoses]
        assert any(s in [Severity.HIGH, Severity.CRITICAL] for s in severities)


# ============================================================================
# Test Agent: Behavioral
# ============================================================================

class TestBehavioralAgent:
    """Tests for BehavioralAgent."""

    def test_diagnose_low_study_hours(self, sample_high_risk_state):
        """Test detection of low study hours."""
        agent = BehavioralAgent()
        diagnoses = agent.diagnose(sample_high_risk_state.behavioral, day=50)

        issue_names = [d.issue_name for d in diagnoses]
        assert "low_study_hours" in issue_names or "low_study_consistency" in issue_names

    def test_diagnose_high_procrastination(self, sample_high_risk_state):
        """Test detection of procrastination."""
        agent = BehavioralAgent()
        diagnoses = agent.diagnose(sample_high_risk_state.behavioral, day=50)

        issue_names = [d.issue_name for d in diagnoses]
        assert "high_procrastination" in issue_names

    def test_no_issues_for_good_behavior(self, sample_low_risk_state):
        """Test that good behavior produces no issues."""
        agent = BehavioralAgent()
        diagnoses = agent.diagnose(sample_low_risk_state.behavioral, day=50)

        assert len(diagnoses) == 0


# ============================================================================
# Test Agent: Recovery
# ============================================================================

class TestRecoveryAgent:
    """Tests for RecoveryAgent."""

    def test_diagnose_sleep_deficit(self, sample_high_risk_state):
        """Test detection of sleep deficit."""
        agent = RecoveryAgent()
        diagnoses = agent.diagnose(
            (sample_high_risk_state.recovery, sample_high_risk_state.engagement),
            day=50
        )

        issue_names = [d.issue_name for d in diagnoses]
        assert "sleep_deficit" in issue_names or "low_sleep" in issue_names

    def test_diagnose_high_stress(self, sample_high_risk_state):
        """Test detection of high stress."""
        agent = RecoveryAgent()
        diagnoses = agent.diagnose(
            (sample_high_risk_state.recovery, sample_high_risk_state.engagement),
            day=50
        )

        issue_names = [d.issue_name for d in diagnoses]
        assert "high_stress" in issue_names

    def test_no_issues_for_good_recovery(self, sample_low_risk_state):
        """Test that good recovery produces no issues."""
        agent = RecoveryAgent()
        diagnoses = agent.diagnose(
            (sample_low_risk_state.recovery, sample_low_risk_state.engagement),
            day=50
        )

        assert len(diagnoses) == 0


# ============================================================================
# Test Agent: Workload
# ============================================================================

class TestWorkloadAgent:
    """Tests for WorkloadAgent."""

    def test_diagnose_high_pending_assignments(self, sample_high_risk_state):
        """Test detection of high pending assignments."""
        agent = WorkloadAgent()
        diagnoses = agent.diagnose(sample_high_risk_state.workload, day=50)

        issue_names = [d.issue_name for d in diagnoses]
        assert "high_pending_assignments" in issue_names

    def test_diagnose_deadline_clustering(self, sample_high_risk_state):
        """Test detection of deadline clustering."""
        agent = WorkloadAgent()
        diagnoses = agent.diagnose(sample_high_risk_state.workload, day=50)

        issue_names = [d.issue_name for d in diagnoses]
        assert any(issue in issue_names for issue in ["deadline_clustering", "high_deadline_density"])

    def test_supported_scenarios(self):
        """Test supported scenarios."""
        agent = WorkloadAgent()
        scenarios = agent.get_supported_scenarios()

        assert "REDUCE_WORKLOAD" in scenarios
        assert "MOVE_ASSIGNMENT" in scenarios


# ============================================================================
# Test Agent: Schedule
# ============================================================================

class TestScheduleAgent:
    """Tests for ScheduleAgent."""

    def test_diagnose_no_issues_for_aligned_mid_semester(self):
        """Test that aligned non-pressure temporal context produces no issues."""
        agent = ScheduleAgent()
        temporal = TemporalContext(
            day_of_semester=50,
            week_of_semester=8,
            day_of_week=0,
            is_exam_period=False,
            is_midterm_period=False,
            semester_phase="mid",
            days_until_exam_period=35,
        )

        diagnoses = agent.diagnose(temporal, day=50)
        assert diagnoses == []

    def test_diagnose_exam_period_overload(self):
        """Test detection of exam-period overload."""
        agent = ScheduleAgent()
        temporal = TemporalContext(
            day_of_semester=86,
            week_of_semester=13,
            day_of_week=1,
            is_exam_period=True,
            is_midterm_period=False,
            semester_phase="exam",
            days_until_exam_period=0,
        )

        diagnoses = agent.diagnose(temporal, day=86)
        issue_names = [d.issue_name for d in diagnoses]

        assert "exam_period_overload" in issue_names
        exam_diagnosis = next(d for d in diagnoses if d.issue_name == "exam_period_overload")
        assert exam_diagnosis.severity == Severity.CRITICAL
        assert "REDUCE_DEADLINE_DENSITY" in exam_diagnosis.suggested_scenario_types

    def test_diagnose_deadline_clustering_window(self):
        """Test detection of exam-adjacent deadline clustering window."""
        agent = ScheduleAgent()
        temporal = TemporalContext(
            day_of_semester=80,
            week_of_semester=12,
            day_of_week=2,
            is_exam_period=False,
            is_midterm_period=False,
            semester_phase="late",
            days_until_exam_period=5,
        )

        diagnoses = agent.diagnose(temporal, day=80)
        issue_names = [d.issue_name for d in diagnoses]

        assert "deadline_clustering_window" in issue_names
        assert "late_semester_scheduling_pressure" in issue_names

    def test_diagnose_temporal_misalignment(self):
        """Test detection of inconsistent temporal fields."""
        agent = ScheduleAgent()
        temporal = TemporalContext(
            day_of_semester=50,
            week_of_semester=1,
            day_of_week=0,
            is_exam_period=True,
            is_midterm_period=False,
            semester_phase="early",
            days_until_exam_period=10,
        )

        diagnoses = agent.diagnose(temporal, day=49)
        issue_names = [d.issue_name for d in diagnoses]

        assert "temporal_misalignment" in issue_names
        misalignment = next(d for d in diagnoses if d.issue_name == "temporal_misalignment")
        assert misalignment.severity in [Severity.HIGH, Severity.CRITICAL]

    def test_supported_scenarios_are_existing_phase5_types(self):
        """Test supported scenarios are existing Phase 5 ScenarioType names."""
        agent = ScheduleAgent()
        scenarios = agent.get_supported_scenarios()
        phase5_names = set(ScenarioType.__members__)

        assert set(scenarios).issubset(phase5_names)
        assert "MOVE_ASSIGNMENT" in scenarios
        assert "REDUCE_DEADLINE_DENSITY" in scenarios

    def test_diagnoses_do_not_generate_probability_fields(self):
        """Test diagnoses remain threshold-based AgentDiagnosis outputs only."""
        agent = ScheduleAgent()
        diagnoses = agent.diagnose(TemporalContext(
            day_of_semester=86,
            week_of_semester=13,
            day_of_week=1,
            is_exam_period=True,
            is_midterm_period=False,
            semester_phase="exam",
            days_until_exam_period=0,
        ), day=86)

        for diagnosis in diagnoses:
            assert not hasattr(diagnosis, "overload_probability")
            assert not hasattr(diagnosis, "risk_probability")


# ============================================================================
# Test Orchestrator
# ============================================================================

class TestOrchestratorAgent:
    """Tests for OrchestratorAgent."""

    def test_initialization(self):
        """Test that orchestrator initializes correctly."""
        orchestrator = OrchestratorAgent()

        assert orchestrator.academic_agent is not None
        assert orchestrator.behavioral_agent is not None
        assert orchestrator.recovery_agent is not None
        assert orchestrator.workload_agent is not None
        assert orchestrator.schedule_agent is not None
        assert orchestrator.llm_reasoner is not None

    def test_agent_statistics(self, sample_high_risk_state):
        """Test agent statistics collection."""
        orchestrator = OrchestratorAgent()
        stats = orchestrator.get_agent_statistics(sample_high_risk_state, day=50)

        assert stats['total_diagnoses'] > 0
        assert 'by_severity' in stats
        assert 'by_agent' in stats
        assert 'top_issues' in stats

    def test_supported_scenarios_list(self):
        """Test listing supported scenarios."""
        orchestrator = OrchestratorAgent()
        scenarios = orchestrator.list_supported_scenarios()

        assert 'AcademicAgent' in scenarios
        assert 'BehavioralAgent' in scenarios
        assert 'RecoveryAgent' in scenarios
        assert 'WorkloadAgent' in scenarios
        assert 'ScheduleAgent' in scenarios

    def test_schedule_agent_runs_with_orchestrator(self):
        """Test ScheduleAgent runs alongside the other specialized agents."""
        orchestrator = OrchestratorAgent()
        state = StudentTwinState(
            student_id="SCHEDULE_001",
            day=86,
            temporal=TemporalContext(
                day_of_semester=86,
                week_of_semester=13,
                day_of_week=1,
                is_exam_period=True,
                is_midterm_period=False,
                semester_phase="exam",
                days_until_exam_period=0,
            ),
        )

        diagnoses = orchestrator._run_specialized_agents(state, day=86, parallel=False)

        assert "ScheduleAgent" in diagnoses
        assert any(d.issue_name == "exam_period_overload" for d in diagnoses["ScheduleAgent"])


# ============================================================================
# Test Phase 6 Temporal Safety
# ============================================================================

class TestPhase6TemporalSafety:
    """Phase 6-specific temporal safety tests."""

    def test_schedule_agent_receives_only_temporal_context(self, sample_low_risk_state):
        """Verify orchestrator passes only TemporalContext to ScheduleAgent."""
        orchestrator = OrchestratorAgent()
        received_layers = []

        def capture_schedule_layer(state_layer, day=0):
            received_layers.append(state_layer)
            return []

        orchestrator.schedule_agent.diagnose = capture_schedule_layer
        orchestrator._run_specialized_agents(sample_low_risk_state, day=50, parallel=False)

        assert len(received_layers) == 1
        assert isinstance(received_layers[0], TemporalContext)
        assert received_layers[0] is sample_low_risk_state.temporal

    def test_orchestrator_flags_future_temporal_context(self, sample_low_risk_state):
        """Verify Phase 6 safety validation rejects a future temporal context."""
        orchestrator = OrchestratorAgent()
        sample_low_risk_state.day = 50
        sample_low_risk_state.temporal.day_of_semester = 51

        is_safe, violations = orchestrator.validate_safety_constraints(
            sample_low_risk_state,
            day=50,
        )

        assert is_safe is False
        assert any("Temporal context day" in violation for violation in violations)


# ============================================================================
# Test LLM Reasoner
# ============================================================================

class TestLLMReasoner:
    """Tests for LLMReasoner."""

    def test_initialization_mock_mode(self):
        """Test that reasoner initializes in mock mode without API key."""
        reasoner = LLMReasoner(api_key=None)
        assert reasoner.use_mock is True

    def test_safety_validation_unsafe_patterns(self):
        """Test detection of unsafe language patterns."""
        reasoner = LLMReasoner(api_key=None)

        unsafe_texts = [
            "This will definitely reduce your stress",
            "This causes lower overload risk",
            "Guaranteed to improve your grades",
        ]

        for text in unsafe_texts:
            assert reasoner._validate_safety(text) is False

    def test_safety_validation_safe_patterns(self):
        """Test that safe language passes validation."""
        reasoner = LLMReasoner(api_key=None)

        # Must include: model-estimated, synthetic data, no causal phrases
        safe_text = (
            "The model-estimated risk reduction is 10%. "
            "This prediction is based on synthetic data and may vary. "
            "Individual results depend on implementation."
        )

        assert reasoner._validate_safety(safe_text) is True


# ============================================================================
# Test Recommendation
# ============================================================================

class TestRecommendation:
    """Tests for Recommendation formatting."""

    def test_recommendation_creation(self):
        """Test creating a recommendation."""
        rec = Recommendation(
            scenario_id="test_001",
            scenario_type="INCREASE_SLEEP",
            scenario_description="Increase sleep to 8 hours",
            baseline_risk=0.75,
            counterfactual_risk=0.65,
            risk_delta=0.10,
            risk_reduction_percentage=13.3,
            explanation="Test explanation",
            primary_diagnoses=["RecoveryAgent: sleep_deficit"],
        )

        assert rec.scenario_id == "test_001"
        assert rec.risk_delta == 0.10
        assert rec.was_successful == True  # risk_delta > 0 means success

    def test_recommendation_formatting(self):
        """Test human-readable formatting."""
        rec = Recommendation(
            scenario_id="test_001",
            scenario_type="INCREASE_SLEEP",
            scenario_description="Increase sleep to 8 hours",
            baseline_risk=0.75,
            counterfactual_risk=0.65,
            risk_delta=0.10,
            risk_reduction_percentage=13.3,
            explanation="The model-estimated impact of increasing sleep is a risk reduction.",
            primary_diagnoses=["RecoveryAgent: sleep_deficit"],
            caveats=["Based on synthetic data", "Model predictions only"],
        )

        formatted = rec.format_for_student()

        assert "Intervention Recommendation" in formatted
        assert "model-estimated" in formatted.lower()
        assert "synthetic data" in formatted.lower()

    def test_recommendation_safety_validation(self):
        """Test safety validation of recommendation."""
        safe_rec = Recommendation(
            scenario_id="test_001",
            scenario_type="INCREASE_SLEEP",
            scenario_description="Increase sleep to 8 hours",
            baseline_risk=0.75,
            counterfactual_risk=0.65,
            risk_delta=0.10,
            risk_reduction_percentage=13.3,
            explanation="The model-estimated impact shows a risk reduction under this scenario based on synthetic data.",
            caveats=["Based on synthetic training data"],
        )

        assert safe_rec.validate_safety() is True


# ============================================================================
# Test Intervention Registry
# ============================================================================

class TestInterventionRegistry:
    """Tests for InterventionRegistry."""

    def test_log_intervention(self):
        """Test logging an intervention."""
        registry = InterventionRegistry(registry_path="test_registry.json")

        rec = Recommendation(
            scenario_id="test_001",
            scenario_type="INCREASE_SLEEP",
            scenario_description="Increase sleep to 8 hours",
            baseline_risk=0.75,
            counterfactual_risk=0.65,
            risk_delta=0.10,
            risk_reduction_percentage=13.3,
            explanation="Test",
            student_id="STU_001",
            day=50,
        )

        intervention_id = registry.log_intervention("STU_001", rec, day=50)

        assert intervention_id in registry.records
        assert registry.records[intervention_id].status == InterventionStatus.OFFERED

    def test_update_student_response(self):
        """Test updating student response."""
        registry = InterventionRegistry(registry_path="test_registry.json")

        rec = Recommendation(
            scenario_id="test_001",
            scenario_type="INCREASE_SLEEP",
            scenario_description="Increase sleep to 8 hours",
            baseline_risk=0.75,
            counterfactual_risk=0.65,
            risk_delta=0.10,
            risk_reduction_percentage=13.3,
            explanation="Test",
            student_id="STU_001",
            day=50,
        )

        intervention_id = registry.log_intervention("STU_001", rec, day=50)
        registry.update_student_response(intervention_id, "accepted", day=50)

        assert registry.records[intervention_id].status == InterventionStatus.ACCEPTED

    def test_acceptance_rate(self):
        """Test acceptance rate calculation."""
        registry = InterventionRegistry(registry_path="test_registry.json")

        rec = Recommendation(
            scenario_id="test_001",
            scenario_type="INCREASE_SLEEP",
            scenario_description="Increase sleep",
            baseline_risk=0.75,
            counterfactual_risk=0.65,
            risk_delta=0.10,
            risk_reduction_percentage=13.3,
            explanation="Test",
            student_id="STU_001",
            day=50,
        )

        id1 = registry.log_intervention("STU_001", rec, day=50)
        registry.update_student_response(id1, "accepted", day=50)

        id2 = registry.log_intervention("STU_001", rec, day=51)
        registry.update_student_response(id2, "rejected", day=51)

        rate = registry.get_acceptance_rate("STU_001")
        assert rate == 0.5


# ============================================================================
# Test Outcome Tracker
# ============================================================================

class TestOutcomeTracker:
    """Tests for OutcomeTracker."""

    def test_start_tracking(self):
        """Test starting outcome tracking."""
        tracker = OutcomeTracker(tracker_path="test_outcomes.json")

        outcome_id = tracker.start_tracking(
            intervention_id="int_001",
            student_id="STU_001",
            baseline_state=None,
            baseline_risk=0.75,
            baseline_strain=0.5,
            predicted_risk_delta=0.10,
            predicted_counterfactual_risk=0.65,
        )

        assert outcome_id in tracker.reports
        assert tracker.reports[outcome_id].baseline_risk == 0.75

    def test_outcome_success_determination(self, sample_high_risk_state):
        """Test success determination."""
        class StubPredictionService:
            def predict(self, followup_state, day=0):
                return SimpleNamespace(overload_probability=0.60, strain_index=0.40)

        tracker = OutcomeTracker(
            tracker_path="test_outcomes.json",
            prediction_service=StubPredictionService(),
        )

        outcome_id = tracker.start_tracking(
            intervention_id="int_001",
            student_id="STU_001",
            baseline_state=None,
            baseline_risk=0.75,
            baseline_strain=0.5,
            predicted_risk_delta=0.10,
            predicted_counterfactual_risk=0.65,
        )

        # Simulate followup with lower risk
        modified_state = sample_high_risk_state
        report = tracker.record_followup(outcome_id, modified_state, followup_day=57)

        assert report.actual_risk_at_day7 is not None
        assert report.was_successful is not None


# ============================================================================
# Test Phase6System (Integration)
# ============================================================================

class TestPhase6System:
    """Integration tests for Phase6System."""

    def test_system_initialization(self):
        """Test system initializes correctly."""
        system = Phase6System()

        assert system.orchestrator is not None
        assert system.registry is not None
        assert system.outcome_tracker is not None

    def test_get_system_statistics(self):
        """Test system statistics."""
        system = Phase6System()
        stats = system.get_system_statistics()

        assert 'registry' in stats
        assert 'outcomes' in stats
        assert 'supported_scenarios' in stats


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])


class TestOrchestrateSimulationPathRegression:
    """Regression: _simulate_scenarios must return CounterfactualResult, not tuples."""

    def test_orchestrate_to_ranking_path_uses_counterfactualresults(self):
        from phase6_orchestrator import Phase6System
        from core.schemas import StudentTwinState, AcademicState, BehavioralState, RecoveryState, WorkloadState, EngagementState, TemporalContext, PredictionSnapshot, HistorySummary

        system = Phase6System()
        state = StudentTwinState(
            student_id="REGRESSION_01", day=50,
            academic=AcademicState(attendance_rate_7d=0.7, missed_deadlines_14d=3, academic_load_score=0.9),
            behavioral=BehavioralState(avg_study_hours_7d=2.0, study_consistency_score=0.35),
            recovery=RecoveryState(avg_sleep_hours_7d=5.2, sleep_deficit_7d_hours=10.0),
            workload=WorkloadState(pending_assignment_count=12, workload_pressure_score_7d=0.85),
            engagement=EngagementState(avg_stress_7d=4.5),
            temporal=TemporalContext(day_of_semester=50),
            predictions=PredictionSnapshot(overload_risk_probability=0.65),
        )
        results = system.orchestrator._simulate_scenarios(
            state, system.orchestrator.scenario_generator.generate(state, 50), 50
        )
        from simulation.counterfactual_engine import CounterfactualResult
        assert all(isinstance(r, CounterfactualResult) for r in results), "_simulate_scenarios must return CounterfactualResult objects"
        # Full ranking path must succeed
        ranked = system.orchestrator.scenario_ranker.rank(results)
        assert isinstance(ranked, list) and len(ranked) > 0
