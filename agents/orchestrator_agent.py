"""
KAIROS-TWIN Phase 6: Orchestrator Agent.

Coordinates all specialized agents and Phase 5 tools:
1. Aggregates diagnoses from all agents
2. Generates scenarios via ScenarioGenerator
3. Simulates scenarios via CounterfactualEngine
4. Ranks scenarios via ScenarioRanker
5. Generates recommendation via LLMReasoner
"""
from __future__ import annotations
from typing import Dict, List, Tuple, Any, Optional
import concurrent.futures

from core.schemas import StudentTwinState
from simulation.prediction_service import PredictionService
from simulation.scenario_generator import ScenarioGenerator
from simulation.counterfactual_engine import CounterfactualEngine, CounterfactualResult
from simulation.scenario_ranker import ScenarioRanker, RankedScenario

from agents.base_agent import BaseAgent, AgentDiagnosis
from agents.academic_agent import AcademicAgent
from agents.behavioral_agent import BehavioralAgent
from agents.recovery_agent import RecoveryAgent
from agents.workload_agent import WorkloadAgent
from agents.schedule_agent import ScheduleAgent
from agents.llm_reasoner import LLMReasoner
from intervention.recommendation import Recommendation, RecommendationConfig


class OrchestratorAgent:
    """
    Orchestrates the entire multi-agent intervention workflow.

    Workflow:
    1. Receive StudentTwinState(t)
    2. Call PredictionService for baseline risk
    3. Run specialized agents in parallel → diagnoses
    4. Generate candidate scenarios (ScenarioGenerator)
    5. Simulate each scenario (CounterfactualEngine)
    6. Rank scenarios (ScenarioRanker)
    7. Generate final recommendation (LLMReasoner)
    8. Return Recommendation

    All Phase 5 tools are used as-is without modification.
    """

    def __init__(
        self,
        llm_reasoner: Optional[LLMReasoner] = None,
        prediction_service: Optional[PredictionService] = None,
        scenario_generator: Optional[ScenarioGenerator] = None,
        counterfactual_engine: Optional[CounterfactualEngine] = None,
        scenario_ranker: Optional[ScenarioRanker] = None,
        config: Optional[RecommendationConfig] = None,
    ):
        """
        Initialize orchestrator with components.

        Args:
            llm_reasoner: LLM reasoner (if None, creates default with mock)
            prediction_service: Prediction service (if None, loads from default)
            scenario_generator: Scenario generator (if None, creates default)
            counterfactual_engine: Counterfactual engine (if None, creates default)
            scenario_ranker: Scenario ranker (if None, creates default)
            config: Recommendation configuration
        """
        # Initialize specialized agents
        self.academic_agent = AcademicAgent()
        self.behavioral_agent = BehavioralAgent()
        self.recovery_agent = RecoveryAgent()
        self.workload_agent = WorkloadAgent()
        self.schedule_agent = ScheduleAgent()

        # Initialize LLM reasoner (with mock if no API key)
        self.llm_reasoner = llm_reasoner or LLMReasoner(api_key=None)  # Mock mode

        # Initialize Phase 5 tools
        self.prediction_service = prediction_service or PredictionService()
        self.scenario_generator = scenario_generator or ScenarioGenerator()
        self.counterfactual_engine = counterfactual_engine or CounterfactualEngine(
            prediction_service=self.prediction_service
        )
        self.scenario_ranker = scenario_ranker or ScenarioRanker()

        # Configuration
        self.config = config or RecommendationConfig()

    def orchestrate(
        self,
        twin_state: StudentTwinState,
        day: int = 0,
        parallel_agents: bool = True,
    ) -> Recommendation:
        """
        Run the full orchestration workflow.

        Args:
            twin_state: StudentTwinState at time t
            day: Current semester day
            parallel_agents: Whether to run agents in parallel

        Returns:
            Final recommendation for the student
        """
        student_id = twin_state.student_id

        # Step 1: Get baseline prediction
        baseline_snapshot = self.prediction_service.predict(twin_state, day)
        baseline_risk = baseline_snapshot.overload_probability
        strain = baseline_snapshot.strain_index

        # Step 2: Run specialized agents
        diagnoses = self._run_specialized_agents(twin_state, day, parallel_agents)

        # Step 3: Generate candidate scenarios
        scenarios = self.scenario_generator.generate(twin_state, day)

        if not scenarios:
            # No scenarios generated → fallback recommendation
            return self.llm_reasoner._create_fallback_recommendation(
                student_id=student_id,
                baseline_risk=baseline_risk,
                diagnoses=diagnoses,
            )

        # Step 4: Simulate scenarios
        counterfactual_results = self._simulate_scenarios(
            twin_state, scenarios, day
        )

        if not counterfactual_results:
            # No valid simulation results
            return self.llm_reasoner._create_fallback_recommendation(
                student_id=student_id,
                baseline_risk=baseline_risk,
                diagnoses=diagnoses,
            )

        # Step 5: Rank scenarios
        ranked_scenarios = self.scenario_ranker.rank(counterfactual_results)

        if not ranked_scenarios:
            # Ranking failed
            return self.llm_reasoner._create_fallback_recommendation(
                student_id=student_id,
                baseline_risk=baseline_risk,
                diagnoses=diagnoses,
            )

        # Step 6: Generate recommendation with LLM
        recommendation = self.llm_reasoner.reason(
            student_id=student_id,
            baseline_risk=baseline_risk,
            strain=strain,
            diagnoses=diagnoses,
            ranked_scenarios=ranked_scenarios,
            config=self.config,
        )

        # Add day to recommendation
        recommendation.day = day

        return recommendation

    def _run_specialized_agents(
        self,
        twin_state: StudentTwinState,
        day: int,
        parallel: bool = True,
    ) -> Dict[str, List[AgentDiagnosis]]:
        """
        Run all specialized agents and collect diagnoses.

        Args:
            twin_state: Student state
            day: Current day
            parallel: Whether to run agents in parallel

        Returns:
            Dict mapping agent name -> list of diagnoses
        """
        diagnoses = {}

        if parallel:
            # Run agents in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    'AcademicAgent': executor.submit(
                        self.academic_agent.diagnose, twin_state.academic, day
                    ),
                    'BehavioralAgent': executor.submit(
                        self.behavioral_agent.diagnose, twin_state.behavioral, day
                    ),
                    'RecoveryAgent': executor.submit(
                        self.recovery_agent.diagnose,
                        (twin_state.recovery, twin_state.engagement),  # tuple
                        day
                    ),
                    'WorkloadAgent': executor.submit(
                        self.workload_agent.diagnose, twin_state.workload, day
                    ),
                    'ScheduleAgent': executor.submit(
                        self.schedule_agent.diagnose, twin_state.temporal, day
                    ),
                }

                for agent_name, future in futures.items():
                    try:
                        result = future.result(timeout=5.0)
                        diagnoses[agent_name] = result
                    except Exception as e:
                        print(f"Warning: {agent_name} failed: {e}")
                        diagnoses[agent_name] = []
        else:
            # Run agents sequentially
            diagnoses['AcademicAgent'] = self.academic_agent.diagnose(
                twin_state.academic, day
            )
            diagnoses['BehavioralAgent'] = self.behavioral_agent.diagnose(
                twin_state.behavioral, day
            )
            diagnoses['RecoveryAgent'] = self.recovery_agent.diagnose(
                (twin_state.recovery, twin_state.engagement),  # tuple
                day
            )
            diagnoses['WorkloadAgent'] = self.workload_agent.diagnose(
                twin_state.workload, day
            )
            diagnoses['ScheduleAgent'] = self.schedule_agent.diagnose(
                twin_state.temporal, day
            )

        return diagnoses

    def _simulate_scenarios(
        self,
        baseline_state: StudentTwinState,
        scenarios: List,
        day: int,
    ) -> List[CounterfactualResult]:
        """
        Simulate all scenarios with CounterfactualEngine.

        Args:
            baseline_state: Original state
            scenarios: List of scenario objects
            day: Current day

        Returns:
            List of CounterfactualResult objects
        """
        results = []

        for scenario in scenarios:
            try:
                result = self.counterfactual_engine.simulate(
                    baseline_state, scenario, day
                )
                if result is not None:
                    results.append(result)
            except Exception as e:
                print(f"Warning: Scenario simulation failed: {e}")

        return results

    def get_agent_statistics(self, twin_state: StudentTwinState, day: int = 0) -> Dict[str, Any]:
        """
        Get statistics about agent diagnoses without running full orchestration.

        Useful for debugging and monitoring.

        Args:
            twin_state: Student state
            day: Current day

        Returns:
            Statistics dict
        """
        diagnoses = self._run_specialized_agents(twin_state, day, parallel=False)

        stats = {
            'total_diagnoses': 0,
            'by_severity': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0},
            'by_agent': {},
            'top_issues': [],
        }

        for agent_name, agent_diagnoses in diagnoses.items():
            stats['by_agent'][agent_name] = len(agent_diagnoses)
            stats['total_diagnoses'] += len(agent_diagnoses)

            for diag in agent_diagnoses:
                # Count by severity
                severity_key = diag.severity.value
                if severity_key in stats['by_severity']:
                    stats['by_severity'][severity_key] += 1

                # Collect top issues (high/critical severity)
                if diag.severity.value in ['high', 'critical']:
                    stats['top_issues'].append({
                        'agent': agent_name,
                        'issue': diag.issue_name,
                        'severity': diag.severity.value,
                        'description': diag.description,
                    })

        return stats

    def list_supported_scenarios(self) -> Dict[str, List[str]]:
        """
        List all scenario types supported by each agent.

        Returns:
            Dict mapping agent name -> list of supported scenario types
        """
        return {
            'AcademicAgent': self.academic_agent.get_supported_scenarios(),
            'BehavioralAgent': self.behavioral_agent.get_supported_scenarios(),
            'RecoveryAgent': self.recovery_agent.get_supported_scenarios(),
            'WorkloadAgent': self.workload_agent.get_supported_scenarios(),
            'ScheduleAgent': self.schedule_agent.get_supported_scenarios(),
        }

    def validate_safety_constraints(self, twin_state: StudentTwinState, day: int = 0) -> Tuple[bool, List[str]]:
        """
        Validate that orchestration respects all safety constraints.

        Args:
            twin_state: Student state
            day: Current day

        Returns:
            (is_safe, list_of_violations)
        """
        violations = []

        # Check that temporal constraints are respected before running tools.
        if twin_state.day != day:
            violations.append(f"State day ({twin_state.day}) doesn't match query day ({day})")
        if twin_state.temporal.day_of_semester > day:
            violations.append(
                f"Temporal context day ({twin_state.temporal.day_of_semester}) exceeds query day ({day})"
            )
        if violations:
            return False, violations

        # Run a test orchestration
        recommendation = self.orchestrate(twin_state, day, parallel_agents=False)

        # Check recommendation safety
        if not recommendation.validate_safety():
            violations.append("Recommendation fails safety validation")

        # Check that no agent invented values
        # (This is more of a process check - actual value invention would be in LLM)
        baseline_snapshot = self.prediction_service.predict(twin_state, day)
        if baseline_snapshot.overload_probability < 0 or baseline_snapshot.overload_probability > 1:
            violations.append("Invalid probability value detected")

        return len(violations) == 0, violations
