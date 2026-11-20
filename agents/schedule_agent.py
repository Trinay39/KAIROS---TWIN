"""
KAIROS-TWIN Phase 6: Schedule Agent.

Analyzes temporal calendar context without reading academic, behavioral,
recovery, workload, engagement, prediction, or history layers.
"""
from __future__ import annotations
from typing import List

from core.schemas import TemporalContext
from simulation.scenario_schema import ScenarioType
from agents.base_agent import BaseAgent, AgentDiagnosis, Severity


class ScheduleAgent(BaseAgent):
    """
    Analyzes scheduling pressure from TemporalContext only.

    Monitors:
    - Deadline clustering windows near exam periods
    - Exam and midterm period overload
    - Temporal context misalignment
    - Late-semester scheduling pressure

    Triggers only existing Phase 5 scenario types:
    - MOVE_ASSIGNMENT
    - REDUCE_DEADLINE_DENSITY
    - REDUCE_WORKLOAD
    """

    SUPPORTED_SCENARIOS = [
        ScenarioType.MOVE_ASSIGNMENT.name,
        ScenarioType.REDUCE_DEADLINE_DENSITY.name,
        ScenarioType.REDUCE_WORKLOAD.name,
    ]

    def __init__(self):
        super().__init__(
            name="ScheduleAgent",
            description="Analyzes temporal context and scheduling pressure"
        )

    def diagnose(self, state_layer: TemporalContext, day: int = 0) -> List[AgentDiagnosis]:
        """
        Analyze temporal context for scheduling issues.

        Args:
            state_layer: TemporalContext object
            day: Current semester day for consistency checks

        Returns:
            List of threshold-based diagnoses (empty if no issues)
        """
        if state_layer is None:
            return []

        diagnoses = []

        diagnoses.extend(self._diagnose_temporal_misalignment(state_layer, day))
        diagnoses.extend(self._diagnose_exam_period_overload(state_layer))
        diagnoses.extend(self._diagnose_deadline_clustering_window(state_layer))
        diagnoses.extend(self._diagnose_late_semester_pressure(state_layer))

        return diagnoses

    def _diagnose_temporal_misalignment(
        self,
        temporal: TemporalContext,
        day: int,
    ) -> List[AgentDiagnosis]:
        """Detect inconsistent day, phase, and period fields."""
        issues = []

        if day and temporal.day_of_semester != day:
            issues.append(f"state day {temporal.day_of_semester} differs from query day {day}")

        expected_week = (temporal.day_of_semester - 1) // 7 + 1
        if temporal.week_of_semester != expected_week:
            issues.append(f"week {temporal.week_of_semester} differs from expected week {expected_week}")

        expected_phase = self._expected_phase(temporal.day_of_semester)
        if temporal.semester_phase != expected_phase:
            issues.append(
                f"phase '{temporal.semester_phase}' differs from expected phase '{expected_phase}'"
            )

        if temporal.is_exam_period != (temporal.day_of_semester >= 85):
            issues.append("exam-period flag is inconsistent with semester day")

        if temporal.is_midterm_period != (29 <= temporal.day_of_semester <= 49):
            issues.append("midterm-period flag is inconsistent with semester day")

        expected_days_until_exam = max(0, 85 - temporal.day_of_semester)
        if temporal.days_until_exam_period != expected_days_until_exam:
            issues.append(
                "days-until-exam field is inconsistent with semester day"
            )

        if not issues:
            return []

        severity = self._classify_severity(
            float(len(issues)),
            {"low": 1.0, "medium": 2.0, "high": 3.0, "critical": 5.0}
        )
        return [self._build_diagnosis(
            issue_name="temporal_misalignment",
            severity=severity,
            description="Temporal context mismatch detected: " + "; ".join(issues),
            affected_fields=[
                "day_of_semester",
                "week_of_semester",
                "is_exam_period",
                "is_midterm_period",
                "semester_phase",
                "days_until_exam_period",
            ],
            suggested_scenario_types=[ScenarioType.REDUCE_DEADLINE_DENSITY.name],
        )]

    def _diagnose_exam_period_overload(
        self,
        temporal: TemporalContext,
    ) -> List[AgentDiagnosis]:
        """Detect exam or midterm period calendar pressure."""
        if temporal.is_exam_period or temporal.semester_phase == "exam":
            return [self._build_diagnosis(
                issue_name="exam_period_overload",
                severity=Severity.CRITICAL,
                description="Current temporal context is in the exam period",
                affected_fields=["is_exam_period", "semester_phase", "day_of_semester"],
                suggested_scenario_types=[
                    ScenarioType.REDUCE_DEADLINE_DENSITY.name,
                    ScenarioType.MOVE_ASSIGNMENT.name,
                    ScenarioType.REDUCE_WORKLOAD.name,
                ],
            )]

        if temporal.is_midterm_period:
            return [self._build_diagnosis(
                issue_name="exam_period_overload",
                severity=Severity.HIGH,
                description="Current temporal context is in the midterm period",
                affected_fields=["is_midterm_period", "semester_phase", "week_of_semester"],
                suggested_scenario_types=[
                    ScenarioType.REDUCE_DEADLINE_DENSITY.name,
                    ScenarioType.MOVE_ASSIGNMENT.name,
                ],
            )]

        return []

    def _diagnose_deadline_clustering_window(
        self,
        temporal: TemporalContext,
    ) -> List[AgentDiagnosis]:
        """
        Detect calendar windows where deadlines should be spread before exams.

        TemporalContext has no assignment counts, so this diagnosis is limited
        to exam-adjacent calendar pressure and does not assert actual deadline
        counts.
        """
        if temporal.is_exam_period:
            return []

        days_until_exam = temporal.days_until_exam_period
        if days_until_exam > 14:
            return []

        severity = self._classify_severity(
            float(14 - days_until_exam),
            {"low": 0.0, "medium": 7.0, "high": 11.0, "critical": 14.0}
        )
        return [self._build_diagnosis(
            issue_name="deadline_clustering_window",
            severity=severity,
            description=(
                f"Temporal context is {days_until_exam} days from exam period; "
                "deadline distribution should be reviewed before exams"
            ),
            affected_fields=["days_until_exam_period", "semester_phase", "day_of_semester"],
            suggested_scenario_types=[
                ScenarioType.REDUCE_DEADLINE_DENSITY.name,
                ScenarioType.MOVE_ASSIGNMENT.name,
            ],
        )]

    def _diagnose_late_semester_pressure(
        self,
        temporal: TemporalContext,
    ) -> List[AgentDiagnosis]:
        """Detect late-semester scheduling pressure from phase/day fields."""
        if temporal.semester_phase != "late" and temporal.day_of_semester < 75:
            return []

        severity = self._classify_severity(
            float(temporal.day_of_semester),
            {"low": 75.0, "medium": 78.0, "high": 82.0, "critical": 85.0}
        )
        return [self._build_diagnosis(
            issue_name="late_semester_scheduling_pressure",
            severity=severity,
            description=f"Semester day {temporal.day_of_semester} is in the late scheduling window",
            affected_fields=["day_of_semester", "semester_phase", "days_until_exam_period"],
            suggested_scenario_types=[
                ScenarioType.REDUCE_DEADLINE_DENSITY.name,
                ScenarioType.MOVE_ASSIGNMENT.name,
                ScenarioType.REDUCE_WORKLOAD.name,
            ],
        )]

    @staticmethod
    def _expected_phase(day_of_semester: int) -> str:
        if day_of_semester < 29:
            return "early"
        if day_of_semester < 57:
            return "mid"
        if day_of_semester < 85:
            return "late"
        return "exam"

    def get_supported_scenarios(self) -> List[str]:
        """Return existing Phase 5 scenario types this agent can trigger."""
        return list(self.SUPPORTED_SCENARIOS)
