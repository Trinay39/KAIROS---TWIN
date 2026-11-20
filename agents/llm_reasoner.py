"""
KAIROS-TWIN Phase 6: LLM Reasoner.

Generates recommendations using Claude API with strict safety constraints:
- No invention or modification of probability values
- No causal claims (use "model estimates", not "causes")
- Must include synthetic data disclaimer
- Must respect scenario ranking from Phase 5

Uses Claude's API with constrained prompts and output validation.
"""
from __future__ import annotations
import re
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

# Try to import Claude API, but fall back gracefully if not available
try:
    from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("Warning: anthropic package not available. LLMReasoner will use mock responses.")

from core.schemas import StudentTwinState
from agents.base_agent import AgentDiagnosis
from intervention.recommendation import Recommendation, RecommendationConfig, RecommendationConfidence
from simulation.counterfactual_engine import CounterfactualResult
from simulation.scenario_ranker import RankedScenario


class LLMReasoner:
    """
    Generates safety-constrained recommendations using Claude API.

    Critical Constraints:
    1. NEVER invent or modify probability values
    2. NEVER claim causal effects ("causes" -> "model estimates")
    3. ALWAYS include limitations (synthetic data, model uncertainty)
    4. Base recommendations ONLY on ranked scenarios provided
    5. Do NOT override ranking without explicit justification

    All outputs are validated with regex checks for safety.
    """

    # Safety validation patterns
    UNSAFE_PATTERNS = [
        r"\bwill\s+(?:reduce|improve|lower|increase|help|cause|solve)\b",
        r"\bguarantee(?:d|s)?\b",
        r"\bcauses?\b",
        r"\bdefinitely\b",
        r"\bcertainly\b",
        r"\babsolutely\b",
        r"\bensures?\b",
        r"\bresults?\s+in\b",
        r"\bleads?\s+to\b",
    ]

    REQUIRED_PATTERNS = [
        r"model[- ]estimated",
        r"model[- ]predicts?",
        r"estimated\s+under",
        r"predicts?\s+that",
        r"predicted\s+impact",
    ]

    DISCLAIMER_PATTERNS = [
        r"\bsynthetic\s+data\b",
        r"\bsimulated\s+data\b",
        r"\bmodel[- ]trained\s+on\s+synthetic\b",
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-sonnet-20240229",
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ):
        """
        Initialize LLM reasoner.

        Args:
            api_key: Anthropic API key (if None, uses mock responses)
            model: Claude model to use
            temperature: Controls randomness (lower = more deterministic)
            max_tokens: Maximum response length
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        if HAS_ANTHROPIC and api_key:
            self.client = Anthropic(api_key=api_key)
            self.use_mock = False
        else:
            self.use_mock = True
            if api_key and not HAS_ANTHROPIC:
                print("Warning: anthropic package not available. Using mock responses.")
            elif not api_key:
                print("Warning: No API key provided. Using mock responses.")

    def reason(
        self,
        student_id: str,
        baseline_risk: float,
        strain: Optional[float],
        diagnoses: Dict[str, List[AgentDiagnosis]],
        ranked_scenarios: List[RankedScenario],
        config: Optional[RecommendationConfig] = None,
    ) -> Recommendation:
        """
        Generate recommendation based on diagnoses and ranked scenarios.

        Args:
            student_id: Student identifier
            baseline_risk: Current overload probability [0, 1]
            strain: Current strain index [0, 1] or None
            diagnoses: Dict mapping agent name -> list of AgentDiagnosis
            ranked_scenarios: Ranked scenarios from Phase 5 ScenarioRanker
            config: Recommendation configuration

        Returns:
            Recommendation object with safety-validated explanation
        """
        if config is None:
            config = RecommendationConfig()

        if not ranked_scenarios:
            return self._create_fallback_recommendation(student_id, baseline_risk, diagnoses)

        # Select top scenario
        top_scenario = ranked_scenarios[0]
        scenario = top_scenario.scenario
        counterfactual_result = top_scenario.result

        # Generate explanation
        explanation = self._generate_explanation(
            student_id=student_id,
            baseline_risk=baseline_risk,
            strain=strain,
            diagnoses=diagnoses,
            scenario=scenario,
            counterfactual_result=counterfactual_result,
        )

        # Validate safety
        if not self._validate_safety(explanation):
            explanation = self._add_safety_disclaimers(explanation)

        # Get primary diagnoses that match this scenario
        primary_diagnoses = self._extract_primary_diagnoses(diagnoses, scenario)

        # Create recommendation
        recommendation = Recommendation.from_counterfactual_result(
            result=counterfactual_result,
            scenario=scenario,
            diagnoses=primary_diagnoses,
            explanation=explanation,
            student_id=student_id,
            day=0,  # Will be set by caller
            config=config,
        )

        return recommendation

    def _generate_explanation(
        self,
        student_id: str,
        baseline_risk: float,
        strain: Optional[float],
        diagnoses: Dict[str, List[AgentDiagnosis]],
        scenario,
        counterfactual_result: CounterfactualResult,
    ) -> str:
        """
        Generate LLM explanation with safety constraints.

        If API is unavailable, returns a mock explanation that meets safety criteria.
        """
        # Prepare diagnoses text
        diagnoses_text = self._format_diagnoses_for_prompt(diagnoses)

        # Prepare scenario text
        scenario_text = self._format_scenario_for_prompt(scenario, counterfactual_result)

        # Build prompt with safety constraints
        prompt = self._build_safe_prompt(
            student_id=student_id,
            baseline_risk=baseline_risk,
            strain=strain,
            diagnoses_text=diagnoses_text,
            scenario_text=scenario_text,
        )

        if self.use_mock:
            # Generate mock explanation that meets safety criteria
            return self._generate_mock_explanation(
                student_id=student_id,
                baseline_risk=baseline_risk,
                diagnoses=diagnoses,
                scenario=scenario,
                counterfactual_result=counterfactual_result,
            )

        # Call Claude API
        try:
            response = self.client.completions.create(
                model=self.model,
                max_tokens_to_sample=self.max_tokens,
                temperature=self.temperature,
                prompt=prompt,
            )
            explanation = response.completion.strip()
        except Exception as e:
            print(f"Warning: LLM call failed: {e}")
            explanation = self._generate_mock_explanation(
                student_id=student_id,
                baseline_risk=baseline_risk,
                diagnoses=diagnoses,
                scenario=scenario,
                counterfactual_result=counterfactual_result,
            )

        return explanation

    def _build_safe_prompt(
        self,
        student_id: str,
        baseline_risk: float,
        strain: Optional[float],
        diagnoses_text: str,
        scenario_text: str,
    ) -> str:
        """
        Build prompt with explicit safety constraints.
        """
        prompt = f"""{HUMAN_PROMPT}
You are a student support assistant helping a student (ID: {student_id})
who has a {baseline_risk:.1%} model-estimated risk of academic overload.

**CRITICAL SAFETY CONSTRAINTS (MUST FOLLOW):**

1. **NEVER invent or modify probability values** - use the values provided exactly.
2. **NEVER claim causal effects** - use "model-estimated", "associated with", "model predicts", NOT "causes", "will reduce", "guaranteed".
3. **ALWAYS acknowledge limitations** - mention synthetic data, model uncertainty.
4. **Base recommendation ONLY on the ranked scenario provided** - do not invent alternatives.
5. **Always use hypothetical language** - "if implemented", "under this scenario".

**Student's Issues (from diagnostic agents):**
{diagnoses_text}

**Top Intervention Scenario:**
{scenario_text}

**Your Task:**
Write a 3-4 sentence explanation recommending this intervention to the student.
Include:
1. What problem(s) it addresses
2. Estimated impact based on model predictions
3. Important limitations/caveats (synthetic data, model uncertainty)

Use model-estimated language. Do not claim causality. Keep it concise and supportive.

**Your response (3-4 sentences):**
{AI_PROMPT}"""

        return prompt

    def _format_diagnoses_for_prompt(self, diagnoses: Dict[str, List[AgentDiagnosis]]) -> str:
        """Format diagnoses for prompt."""
        lines = []
        for agent_name, agent_diagnoses in diagnoses.items():
            if agent_diagnoses:
                lines.append(f"- {agent_name}:")
                for diag in agent_diagnoses:
                    lines.append(f"  * {diag.description} ({diag.severity.value} severity)")
        return "\n".join(lines) if lines else "No significant issues detected by agents."

    def _format_scenario_for_prompt(self, scenario, result: CounterfactualResult) -> str:
        """Format scenario for prompt."""
        scenario_desc = getattr(scenario, 'description', str(scenario))
        risk_delta = abs(result.risk_delta)
        risk_reduction = result.risk_reduction_percentage

        lines = [
            f"- Type: {scenario.scenario_type.value}",
            f"- Description: {scenario_desc}",
            f"- Model-estimated risk reduction: {risk_delta:.1%} ({risk_reduction:.1%} relative reduction)",
        ]

        if hasattr(result, 'changed_features_count') and result.changed_features_count > 0:
            lines.append(f"- Changes {result.changed_features_count} factors in the model")

        return "\n".join(lines)

    def _generate_mock_explanation(
        self,
        student_id: str,
        baseline_risk: float,
        diagnoses: Dict[str, List[AgentDiagnosis]],
        scenario,
        counterfactual_result: CounterfactualResult,
    ) -> str:
        """
        Generate a mock explanation that meets all safety criteria.
        """
        # Get top diagnosis
        top_diagnoses = []
        for agent_diags in diagnoses.values():
            for diag in agent_diags:
                if diag.severity.value in ['high', 'critical']:
                    top_diagnoses.append(diag.description)

        # Simplified description
        if not top_diagnoses:
            top_diagnoses = ["multiple indicators of academic strain"]

        risk_delta = abs(counterfactual_result.risk_delta)
        scenario_desc = getattr(scenario, 'description', "the suggested schedule adjustment")

        explanation = (
            f"Based on our diagnostic agents, we see {', '.join(top_diagnoses[:2])}. "
            f"The model-estimated impact of {scenario_desc} is a {risk_delta:.1%} reduction "
            f"in predicted overload risk (from {baseline_risk:.1%} to {counterfactual_result.counterfactual_prediction.overload_probability:.1%}). "
            f"This is a model prediction based on synthetic training data. "
            f"Actual outcomes may vary for individual students."
        )

        return explanation

    def _validate_safety(self, text: str) -> bool:
        """Validate text meets safety constraints."""
        text_lower = text.lower()

        # Check for unsafe patterns
        for pattern in self.UNSAFE_PATTERNS:
            if re.search(pattern, text_lower):
                return False

        # Check for required patterns
        has_required = any(re.search(pattern, text_lower) for pattern in self.REQUIRED_PATTERNS)
        if not has_required:
            return False

        # Check for disclaimer
        has_disclaimer = any(re.search(pattern, text_lower) for pattern in self.DISCLAIMER_PATTERNS)
        if not has_disclaimer:
            return False

        return True

    def _add_safety_disclaimers(self, text: str) -> str:
        """Add safety disclaimers to potentially unsafe text."""
        lines = [text]
        lines.append("")
        lines.append("(Note: This is a model-estimated association based on synthetic training data. Not a causal claim.)")
        lines.append("(Individual results may vary.)")
        return "\n".join(lines)

    def _extract_primary_diagnoses(
        self,
        diagnoses: Dict[str, List[AgentDiagnosis]],
        scenario,
    ) -> List[str]:
        """Extract diagnoses relevant to this scenario."""
        if hasattr(scenario, 'scenario_type'):
            scenario_values = {
                scenario.scenario_type.value,
                scenario.scenario_type.name,
            }
        else:
            scenario_values = {str(scenario)}

        primary = []
        for agent_name, agent_diagnoses in diagnoses.items():
            for diag in agent_diagnoses:
                # Check if this diagnosis suggests this scenario type
                if scenario_values.intersection(set(diag.suggested_scenario_types)):
                    primary.append(f"{agent_name}: {diag.issue_name}")

        # If no matches, include top severity diagnoses
        if not primary:
            all_diags = []
            for agent_name, agent_diagnoses in diagnoses.items():
                for diag in agent_diagnoses:
                    if diag.severity.value in ['high', 'critical']:
                        all_diags.append((diag.severity.value, f"{agent_name}: {diag.issue_name}"))

            # Sort by severity
            all_diags.sort(key=lambda x: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}[x[0]])
            primary = [diag[1] for diag in all_diags[:2]]

        return primary[:3]  # Limit to top 3

    def _create_fallback_recommendation(
        self,
        student_id: str,
        baseline_risk: float,
        diagnoses: Dict[str, List[AgentDiagnosis]],
    ) -> Recommendation:
        """
        Create fallback recommendation when no scenarios are available.
        """
        explanation = (
            f"Model-estimated overload risk is {baseline_risk:.1%} based on synthetic data only. "
            f"No specific intervention recommended; continue monitoring academic indicators."
        )

        # Create minimal recommendation
        return Recommendation(
            scenario_id="no_intervention",
            scenario_type="MONITOR_ONLY",
            scenario_description="Continue current approach with monitoring",
            baseline_risk=baseline_risk,
            counterfactual_risk=baseline_risk,
            risk_delta=0.0,
            risk_reduction_percentage=0.0,
            explanation=explanation,
            primary_diagnoses=["Monitoring recommended"],
            confidence=RecommendationConfidence.LOW,
            caveats=[
                "No specific intervention recommended",
                "Continue current academic practices",
                "Based on model-estimated predictions from synthetic data only.",
            ],
            student_id=student_id,
        )
