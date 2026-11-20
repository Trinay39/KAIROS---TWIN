"""
KAIROS-TWIN Phase 5: Scenario Schema.

Defines typed scenario representation for counterfactual simulation.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime


class ScenarioType(Enum):
    """Supported scenario types."""
    MOVE_ASSIGNMENT = "move_assignment"
    REMOVE_ASSIGNMENT = "remove_assignment"
    REDUCE_WORKLOAD = "reduce_workload"
    INCREASE_STUDY_TIME = "increase_study_time"
    INCREASE_SLEEP = "increase_sleep"
    REDUCE_DEADLINE_DENSITY = "reduce_deadline_density"


@dataclass
class Scenario:
    """Typed scenario representation."""

    scenario_id: str
    scenario_type: ScenarioType
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    affected_state_variables: List[str] = field(default_factory=list)
    feasibility_metadata: Dict[str, Any] = field(default_factory=dict)
    human_readable_explanation: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert scenario to dictionary."""
        return {
            'scenario_id': self.scenario_id,
            'scenario_type': self.scenario_type.value,
            'description': self.description,
            'parameters': self.parameters,
            'affected_state_variables': self.affected_state_variables,
            'feasibility_metadata': self.feasibility_metadata,
            'human_readable_explanation': self.human_readable_explanation,
            'created_at': self.created_at.isoformat(),
        }


def create_move_assignment_scenario(
    assignment_id: str,
    from_day: int,
    to_day: int,
    current_day: int
) -> Scenario:
    """
    Create MOVE_ASSIGNMENT scenario.

    Args:
        assignment_id: Unique assignment identifier
        from_day: Current due date
        to_day: New due date
        current_day: Current day in semester

    Returns:
        Scenario object

    Raises:
        ValueError: If trying to move assignment to past
    """
    if to_day <= current_day:
        raise ValueError(
            f"Cannot move assignment to past. Current day: {current_day}, "
            f"new date: {to_day}"
        )

    if from_day <= current_day:
        raise ValueError(
            f"Cannot move historical assignment. Assignment due: {from_day}, "
            f"current day: {current_day}"
        )

    return Scenario(
        scenario_id=f"move_assignment_{assignment_id}_{from_day}_to_{to_day}",
        scenario_type=ScenarioType.MOVE_ASSIGNMENT,
        description=f"Move assignment {assignment_id} from day {from_day} to day {to_day}",
        parameters={
            'assignment_id': assignment_id,
            'from_day': from_day,
            'to_day': to_day,
        },
        affected_state_variables=[
            'pending_assignment_count',
            'deadline_density_trend_7d',
            'workload_pressure_score_7d',
            'effort_study_gap_7d',
            'submission_related_features',
        ],
        feasibility_metadata={
            'requires_instructor_approval': True,
            'risk_level': 'low',
        },
        human_readable_explanation=(
            f"The model estimates lower overload risk if assignment {assignment_id} "
            f"is moved from day {from_day} to day {to_day}, potentially reducing "
            f"deadline density and workload pressure."
        ),
    )


def create_remove_assignment_scenario(
    assignment_id: str,
    due_day: int,
    current_day: int
) -> Scenario:
    """
    Create REMOVE_ASSIGNMENT scenario.

    Args:
        assignment_id: Unique assignment identifier
        due_day: Current due date
        current_day: Current day in semester

    Returns:
        Scenario object

    Raises:
        ValueError: If trying to remove already-due assignment
    """
    if due_day <= current_day:
        raise ValueError(
            f"Cannot remove already-due assignment. Due: {due_day}, "
            f"current: {current_day}"
        )

    return Scenario(
        scenario_id=f"remove_assignment_{assignment_id}",
        scenario_type=ScenarioType.REMOVE_ASSIGNMENT,
        description=f"Remove assignment {assignment_id} (due day {due_day})",
        parameters={
            'assignment_id': assignment_id,
            'due_day': due_day,
        },
        affected_state_variables=[
            'pending_assignment_count',
            'deadline_density_trend_7d',
            'workload_pressure_score_7d',
            'effort_study_gap_7d',
        ],
        feasibility_metadata={
            'requires_instructor_approval': True,
            'risk_level': 'very_high',
        },
        human_readable_explanation=(
            f"The model estimates lower overload risk if assignment {assignment_id} "
            f"is removed entirely, reducing overall workload."
        ),
    )


def create_reduce_workload_scenario(
    reduction_pct: float,
    current_day: int
) -> Scenario:
    """
    Create REDUCE_WORKLOAD scenario (generic workload reduction).

    Args:
        reduction_pct: Percentage reduction (0-100)
        current_day: Current day in semester

    Returns:
        Scenario object
    """
    return Scenario(
        scenario_id=f"reduce_workload_{reduction_pct}pct_day{current_day}",
        scenario_type=ScenarioType.REDUCE_WORKLOAD,
        description=f"Reduce workload by {reduction_pct}%",
        parameters={'reduction_pct': reduction_pct},
        affected_state_variables=[
            'pending_assignment_count',
            'pending_assignment_effort_hours',
            'deadline_density_trend_7d',
            'workload_pressure_score_7d',
            'effort_study_gap_7d',
        ],
        feasibility_metadata={
            'requires_instructor_approval': True,
            'risk_level': 'medium',
        },
        human_readable_explanation=(
            f"The model estimates lower overload risk if workload is reduced by {reduction_pct}%, "
            f"decreasing overall pressure and effort requirements."
        ),
    )


def create_increase_study_time_scenario(
    hours_per_day: float,
    days: int,
    current_day: int
) -> Scenario:
    """
    Create INCREASE_STUDY_TIME scenario.

    Args:
        hours_per_day: Additional study hours per day
        days: Number of days to apply this
        current_day: Current day in semester

    Returns:
        Scenario object
    """
    return Scenario(
        scenario_id=f"increase_study_{hours_per_day}h_{days}d_day{current_day}",
        scenario_type=ScenarioType.INCREASE_STUDY_TIME,
        description=(
            f"Student increases study time by {hours_per_day} hours/day for {days} days"
        ),
        parameters={
            'hours_per_day': hours_per_day,
            'days': days,
        },
        affected_state_variables=[
            'avg_study_hours_3d',
            'avg_study_hours_7d',
            'study_consistency_score',
            'effort_study_gap_7d',
        ],
        feasibility_metadata={
            'requires_student_action': True,
            'risk_level': 'low',
            'sustainability': 'uncertain',
        },
        human_readable_explanation=(
            f"The model estimates potentially lower overload risk if the student "
            f"increases study time by {hours_per_day} hours/day for {days} days, "
            f"improving effort-study balance."
        ),
    )


def create_increase_sleep_scenario(
    hours_per_night: float,
    current_day: int
) -> Scenario:
    """
    Create INCREASE_SLEEP scenario.

    Args:
        hours_per_night: Target sleep hours per night
        current_day: Current day in semester

    Returns:
        Scenario object
    """
    return Scenario(
        scenario_id=f"increase_sleep_{hours_per_night}h_day{current_day}",
        scenario_type=ScenarioType.INCREASE_SLEEP,
        description=f"Student improves sleep to {hours_per_night} hours/night",
        parameters={'hours_per_night': hours_per_night},
        affected_state_variables=[
            'avg_sleep_hours_7d',
            'sleep_variability_7d',
            'sleep_deficit_7d_hours',
            'recovery_score_7d',
            'recovery_ratio_7d',
        ],
        feasibility_metadata={
            'requires_student_action': True,
            'risk_level': 'low',
            'sustainability': 'high',
        },
        human_readable_explanation=(
            f"The model estimates lower overload risk if the student improves sleep "
            f"to {hours_per_night} hours/night, enhancing recovery and reducing stress."
        ),
    )


def create_reduce_deadline_density_scenario(
    current_day: int
) -> Scenario:
    """
    Create REDUCE_DEADLINE_DENSITY scenario (spread deadlines).

    Args:
        current_day: Current day in semester

    Returns:
        Scenario object
    """
    return Scenario(
        scenario_id=f"reduce_deadline_density_day{current_day}",
        scenario_type=ScenarioType.REDUCE_DEADLINE_DENSITY,
        description="Spread deadlines to reduce density peaks",
        parameters={},
        affected_state_variables=[
            'deadline_density_trend_7d',
            'deadline_density_next_7_known',
            'workload_pressure_score_7d',
            'effort_study_gap_7d',
        ],
        feasibility_metadata={
            'requires_instructor_coordination': True,
            'risk_level': 'medium',
        },
        human_readable_explanation=(
            "The model estimates lower overload risk if deadlines are spread more evenly, "
            "reducing peak workload pressure and allowing better preparation."
        ),
    )
