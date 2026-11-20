"""
KAIROS-TWIN Phase 6 Examples and Usage Patterns.

This file demonstrates common workflows and patterns for using the
multi-agent intervention system.
"""

# Example 1: Generate a recommendation for a high-risk student
print("""
================================================================================
EXAMPLE 1: Generate Intervention Recommendation
================================================================================

from phase6_orchestrator import Phase6System
from core.schemas import StudentTwinState

# Initialize system
system = Phase6System()

# Get student's current state (typically from TwinEngine)
twin_state = get_student_state(student_id="STU_001", day=50)

# Generate recommendation
recommendation = system.recommend_intervention(twin_state, day=50)

# Present to student
print(recommendation.format_for_student())

# Output:
# ## Intervention Recommendation
# **Option:** Increase sleep to 8 hours per night
# 
# **Estimated impact:**
# - Model-estimated risk under this scenario: 62.0%
# - Risk reduction: 12.0% (from 74.0%)
# - Strain index reduction: 0.087
# 
# **Why this might help:**
# - RecoveryAgent: sleep_deficit
# - WorkloadAgent: high_workload_pressure
# 
# **Explanation:**
# Our diagnostic agents identified a significant sleep deficit...
# (etc.)
""")

# Example 2: Log student response and track outcome
print("""
================================================================================
EXAMPLE 2: Track Intervention Outcome
================================================================================

# Log the intervention with student's response
intervention_id = system.log_intervention(
    recommendation=recommendation,
    student_response="accepted",
    feedback="I'll aim for 8 hours tonight"
)

# ... 7 days pass ...

# Re-compute student state at day+7
followup_state = get_student_state(student_id="STU_001", day=57)

# Track actual outcome
outcome_id = system.track_outcome(
    intervention_id=intervention_id,
    followup_state=followup_state,
    followup_day=57,
    student_feedback="helped",
    student_feedback_text="I feel more focused and got my work done"
)

# Get outcome report
outcome = system.outcome_tracker.get_report(outcome_id)
print(outcome.format_summary())

# Output:
# ## Outcome Report
# **Student:** STU_001
# **Period:** Day 50 → Day 57
#
# **Predicted Impact:**
# - Risk reduction: 12.0%
# - Target risk: 62.0%
#
# **Actual Impact:**
# - Risk change: +14.2% (from 74.0% to 59.8%)
# - Success: Yes
# - Prediction accuracy: 2.2% error
#
# **Observed State Changes:**
# - avg_sleep_hours_7d: 5.5 → 7.9
# - sleep_deficit_7d_hours: 12.0 → 1.0
# - stress_level: 0.85 → 0.65
#
# **Student Self-Report:** helped
#   "I feel more focused and got my work done"
""")

# Example 3: Get student history
print("""
================================================================================
EXAMPLE 3: View Student Intervention History
================================================================================

# Get complete history for a student
history = system.get_student_history("STU_001")

print(f"Total interventions: {history['total_interventions']}")
print(f"Acceptance rate: {history['acceptance_rate']:.1%}")
print(f"Success rate: {history['success_rate']:.1%}")

# Output:
# Total interventions: 5
# Acceptance rate: 80.0%
# Success rate: 75.0%

# Inspect individual interventions
for intervention in history['interventions']:
    print(f"  Day {intervention['offered_at_day']}: {intervention['scenario_type']}")
    if intervention['student_response'] == 'accepted':
        print(f"    -> Accepted, actual impact: {intervention['actual_risk_delta']:+.1%}")
""")

# Example 4: System-wide statistics
print("""
================================================================================
EXAMPLE 4: System-Wide Statistics and Analytics
================================================================================

# Get global system statistics
stats = system.get_system_statistics()

print("Registry Statistics:")
print(f"  Total interventions offered: {stats['registry']['total_interventions']}")
print(f"  Overall acceptance rate: {stats['registry']['acceptance_rate']:.1%}")
print(f"  Overall completion rate: {stats['registry']['completion_rate']:.1%}")

print("\\nOutcome Tracking:")
print(f"  Outcomes tracked: {stats['outcomes']['total_tracked']}")
print(f"  Overall success rate: {stats['outcomes']['success_rate']:.1%}")
print(f"  Mean prediction error: {stats['outcomes']['prediction_accuracy']['mean_error']:.1%}")

print("\\nBy Scenario Type:")
for scenario_type, counts in stats['registry']['by_scenario_type'].items():
    acceptance = counts['accepted'] / counts['offered'] if counts['offered'] > 0 else 0
    print(f"  {scenario_type}: {counts['offered']} offered, {acceptance:.1%} accepted")
""")

# Example 5: Agent diagnosis inspection (debugging)
print("""
================================================================================
EXAMPLE 5: Inspect Agent Diagnoses (Debugging)
================================================================================

# Get agent statistics without running full orchestration
agent_stats = system.orchestrator.get_agent_statistics(twin_state, day=50)

print(f"Total diagnoses: {agent_stats['total_diagnoses']}")
print(f"By severity: {agent_stats['by_severity']}")

print("\\nTop issues:")
for issue in agent_stats['top_issues'][:3]:
    print(f"  [{issue['severity']}] {issue['agent']}: {issue['description']}")

# Output:
# Total diagnoses: 6
# By severity: {'low': 0, 'medium': 1, 'high': 3, 'critical': 2}
#
# Top issues:
#   [critical] RecoveryAgent: Sleep deficit of 12.0 hours over 7 days
#   [critical] WorkloadAgent: high workload pressure (0.88)
#   [high] AcademicAgent: grade deterioration at -0.04 per day
""")

# Example 6: Safety validation
print("""
================================================================================
EXAMPLE 6: Validate Safety Constraints
================================================================================

# Validate that system respects all safety constraints
is_safe = system.validate_safety(twin_state, day=50)

if is_safe:
    print("✓ All safety checks passed")
    print("  - No causal claims detected")
    print("  - No probability value invention")
    print("  - Synthetic data disclaimers present")
    print("  - Temporal constraints respected")
else:
    print("✗ Safety violations detected")
    # (violations would be printed by validate_safety)
""")

# Example 7: Batch processing multiple students
print("""
================================================================================
EXAMPLE 7: Batch Process Multiple Students
================================================================================

from concurrent.futures import ThreadPoolExecutor

# Get states for multiple students
students = get_all_students()
twin_states = [get_student_state(s.id, day=50) for s in students]

system = Phase6System()
recommendations = []

# Process in parallel
with ThreadPoolExecutor(max_workers=8) as executor:
    futures = [
        executor.submit(system.recommend_intervention, state, day=50)
        for state in twin_states
    ]
    recommendations = [f.result() for f in futures]

# Log all interventions
for recommendation in recommendations:
    system.log_intervention(recommendation, student_response="auto_present")

print(f"Processed {len(recommendations)} students")
""")

# Example 8: Custom configuration
print("""
================================================================================
EXAMPLE 8: Custom Recommendation Configuration
================================================================================

from intervention.recommendation import RecommendationConfig

# Create custom config
config = RecommendationConfig(
    include_caveats=True,
    include_confidence=True,
    include_risk_delta=True,
    max_recommendations=2,  # Only show top 2 scenarios
    always_include_synthetic_disclaimer=True,
    language_constraints={
        "no_causal_claims": True,
        "no_value_invention": True,
        "model_estimated_prefix": True,
        "hypothetical_language": True,
    }
)

# Use custom config
system = Phase6System(config=config)
recommendation = system.recommend_intervention(twin_state, day=50)
""")

# Example 9: Accessing Phase 5 tools directly
print("""
================================================================================
EXAMPLE 9: Using Phase 5 Tools Directly
================================================================================

# You can also use Phase 5 tools directly through the orchestrator

# Get prediction
prediction = system.prediction_service.predict(twin_state, day=50)
print(f"Overload risk: {prediction.overload_probability:.1%}")
print(f"Strain index: {prediction.strain_index:.2f}")

# Generate scenarios
scenarios = system.scenario_generator.generate(twin_state, day=50)
print(f"Generated {len(scenarios)} candidate scenarios")

# Simulate a specific scenario
for scenario in scenarios[:1]:
    result = system.counterfactual_engine.simulate(twin_state, scenario, day=50)
    print(f"Scenario: {scenario.scenario_type.value}")
    print(f"  Risk delta: {result.risk_delta:+.1%}")
    print(f"  Changed features: {result.changed_features_count}")
""")

# Example 10: Multi-agent reasoning
print("""
================================================================================
EXAMPLE 10: Understanding Multi-Agent Reasoning
================================================================================

# Each agent independently diagnoses problems:

# 1. AcademicAgent reads academic layer
academic_diagnoses = system.orchestrator.academic_agent.diagnose(
    twin_state.academic, day=50
)
print(f"Academic diagnoses: {[d.issue_name for d in academic_diagnoses]}")

# 2. BehavioralAgent reads behavioral layer
behavioral_diagnoses = system.orchestrator.behavioral_agent.diagnose(
    twin_state.behavioral, day=50
)
print(f"Behavioral diagnoses: {[d.issue_name for d in behavioral_diagnoses]}")

# 3. RecoveryAgent reads recovery + engagement layers
recovery_diagnoses = system.orchestrator.recovery_agent.diagnose(
    (twin_state.recovery, twin_state.engagement), day=50
)
print(f"Recovery diagnoses: {[d.issue_name for d in recovery_diagnoses]}")

# 4. WorkloadAgent reads workload layer
workload_diagnoses = system.orchestrator.workload_agent.diagnose(
    twin_state.workload, day=50
)
print(f"Workload diagnoses: {[d.issue_name for d in workload_diagnoses]}")

# All diagnoses are aggregated and used to:
# - Suggest relevant scenarios
# - Rank scenarios by impact
# - Generate LLM explanation
""")
