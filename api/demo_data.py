"""
Demo mode synthetic historical observation windows.

Provides deterministic observation history for demo profiles so TwinEngine
can compute rolling metrics (study consistency, recovery score, workload
pressure, engagement composite, etc).

All observations use the canonical Phase 3 schema:
  study_hours, sleep_hours, stress_level, grade, attendance_rate, missed_deadline_observed, day
"""
from typing import Callable, List, Dict, Any, Optional


def _profiles() -> Dict[str, Callable[[int], Dict[str, Any]]]:
    return {
        'STU_BALANCED': _balanced_day,
        'STU_PRESSURE': _pressure_day,
        'STU_OVERLOADED': _overloaded_day,
        'STU_RECOVERY': _recovery_day,
        'STU_DEADLINE': _deadline_day,
    }


def has_demo_history(student_id: str) -> bool:
    """Return whether a deterministic demo history exists for this student."""
    return student_id in _profiles()


def get_demo_history_to_day(student_id: str, current_day: int) -> Optional[List[Dict[str, Any]]]:
    """
    Generate deterministic demo observations from day 1 through current_day.

    Unknown students return None so callers can preserve user-supplied data
    without fabricating a history.
    """
    generator = _profiles().get(student_id)
    if generator is None:
        return None
    return [generator(day) for day in range(1, current_day + 1)]


def get_demo_history_window(student_id: str, current_day: int) -> List[Dict[str, Any]]:
    """
    Generate a 7-day synthetic observation window for a demo student.

    Args:
        student_id: Demo student identifier
        current_day: Current day of semester

    Returns:
        List of observations (days current_day-6 through current_day)
    """
    history = get_demo_history_to_day(student_id, current_day)
    if history is None:
        history = [_balanced_day(day) for day in range(1, current_day + 1)]
    return history[-7:]


def _with_common(
    day: int,
    study_hours: float,
    sleep_hours: float,
    stress_level: float,
    grade: float,
    attendance_rate: float,
    missed_deadline_observed: int,
    pending_assignments: int,
    upcoming_deadlines_7d: int,
    workload_pressure: float,
    engagement_score: float,
    platform_interactions: int,
) -> Dict[str, Any]:
    return {
        'day': day,
        'study_hours': study_hours,
        'sleep_hours': sleep_hours,
        'stress_level': stress_level,
        'grade': grade,
        'attendance_rate': attendance_rate,
        'missed_deadline_observed': missed_deadline_observed,
        'pending_assignments': pending_assignments,
        'upcoming_deadlines_7d': upcoming_deadlines_7d,
        'workload_pressure': workload_pressure,
        'engagement_score': engagement_score,
        'platform_interactions': platform_interactions,
        'assignment_due_today': 1 if missed_deadline_observed else 0,
    }


def _balanced_day(day: int) -> Dict[str, Any]:
    study = [4.2, 4.5, 4.0, 4.8, 4.1, 4.3, 4.5][(day - 1) % 7]
    sleep = [7.8, 8.1, 7.9, 8.2, 7.7, 8.0, 8.0][(day - 1) % 7]
    return _with_common(day, study, sleep, 2, 84 + (day % 3), 0.95, 0, 3, 1, 0.30, 0.78, 26)


def _pressure_day(day: int) -> Dict[str, Any]:
    study = [6.8, 7.2, 7.0, 7.5, 6.9, 7.1, 7.5][(day - 1) % 7]
    sleep = [6.2, 6.0, 6.1, 5.9, 6.2, 6.0, 6.2][(day - 1) % 7]
    stress = [5, 6, 5, 6, 5, 6, 6][(day - 1) % 7]
    missed = 1 if day % 14 == 0 else 0
    return _with_common(day, study, sleep, stress, 76 - (day % 4), 0.90, missed, 8, 4, 0.72, 0.55, 17)


def _overloaded_day(day: int) -> Dict[str, Any]:
    study = [2.1, 2.8, 1.9, 2.3, 2.0, 2.6, 2.5][(day - 1) % 7]
    sleep = [4.8, 5.1, 4.9, 5.0, 4.7, 5.0, 5.0][(day - 1) % 7]
    stress = [8, 9, 9, 8, 9, 9, 9][(day - 1) % 7]
    missed = 1 if day % 4 in {0, 1} else 0
    return _with_common(day, study, sleep, stress, 55 - (day % 6), 0.70, missed, 13, 6, 0.88, 0.34, 9)


def _recovery_day(day: int) -> Dict[str, Any]:
    study = [3.5, 3.8, 4.0, 4.1, 3.9, 4.0, 4.0][(day - 1) % 7]
    sleep = [8.3, 8.4, 8.2, 8.1, 8.3, 8.2, 8.2][(day - 1) % 7]
    stress = [4, 4, 3, 3, 4, 3, 4][(day - 1) % 7]
    return _with_common(day, study, sleep, stress, 70 + (day % 4), 0.88, 0, 5, 2, 0.45, 0.68, 21)


def _deadline_day(day: int) -> Dict[str, Any]:
    study = [5.8, 6.2, 6.0, 6.1, 5.9, 6.0, 6.0][(day - 1) % 7]
    sleep = [5.9, 5.7, 5.8, 5.9, 5.8, 5.9, 5.8][(day - 1) % 7]
    stress = [7, 7, 7, 8, 7, 8, 8][(day - 1) % 7]
    missed = 1 if day % 7 in {0, 3} else 0
    return _with_common(day, study, sleep, stress, 77 + (day % 2), 0.85, missed, 10, 5, 0.80, 0.48, 14)


def _balanced_history(current_day: int) -> List[Dict[str, Any]]:
    """NORMAL STUDENT: Balanced study, good sleep, low stress."""
    base_day = max(1, current_day - 6)
    return [
        {'day': base_day + 0, 'study_hours': 4.2, 'sleep_hours': 7.8, 'stress_level': 2, 'grade': 84, 'attendance_rate': 0.95, 'missed_deadline_observed': 0},
        {'day': base_day + 1, 'study_hours': 4.5, 'sleep_hours': 8.1, 'stress_level': 2, 'grade': 85, 'attendance_rate': 0.96, 'missed_deadline_observed': 0},
        {'day': base_day + 2, 'study_hours': 4.0, 'sleep_hours': 7.9, 'stress_level': 2, 'grade': 84, 'attendance_rate': 0.95, 'missed_deadline_observed': 0},
        {'day': base_day + 3, 'study_hours': 4.8, 'sleep_hours': 8.2, 'stress_level': 2, 'grade': 86, 'attendance_rate': 0.97, 'missed_deadline_observed': 0},
        {'day': base_day + 4, 'study_hours': 4.1, 'sleep_hours': 7.7, 'stress_level': 2, 'grade': 84, 'attendance_rate': 0.94, 'missed_deadline_observed': 0},
        {'day': base_day + 5, 'study_hours': 4.3, 'sleep_hours': 8.0, 'stress_level': 2, 'grade': 85, 'attendance_rate': 0.96, 'missed_deadline_observed': 0},
        {'day': current_day, 'study_hours': 4.5, 'sleep_hours': 8.0, 'stress_level': 2, 'grade': 86, 'attendance_rate': 0.95, 'missed_deadline_observed': 0},
    ]


def _pressure_history(current_day: int) -> List[Dict[str, Any]]:
    """AT-RISK STUDENT: High study load, moderate sleep deficit, elevated stress."""
    base_day = max(1, current_day - 6)
    return [
        {'day': base_day + 0, 'study_hours': 6.8, 'sleep_hours': 6.2, 'stress_level': 5, 'grade': 76, 'attendance_rate': 0.90, 'missed_deadline_observed': 0},
        {'day': base_day + 1, 'study_hours': 7.2, 'sleep_hours': 6.0, 'stress_level': 6, 'grade': 75, 'attendance_rate': 0.89, 'missed_deadline_observed': 0},
        {'day': base_day + 2, 'study_hours': 7.0, 'sleep_hours': 6.1, 'stress_level': 5, 'grade': 76, 'attendance_rate': 0.91, 'missed_deadline_observed': 0},
        {'day': base_day + 3, 'study_hours': 7.5, 'sleep_hours': 5.9, 'stress_level': 6, 'grade': 74, 'attendance_rate': 0.88, 'missed_deadline_observed': 1},
        {'day': base_day + 4, 'study_hours': 6.9, 'sleep_hours': 6.2, 'stress_level': 5, 'grade': 75, 'attendance_rate': 0.90, 'missed_deadline_observed': 0},
        {'day': base_day + 5, 'study_hours': 7.1, 'sleep_hours': 6.0, 'stress_level': 6, 'grade': 74, 'attendance_rate': 0.89, 'missed_deadline_observed': 0},
        {'day': current_day, 'study_hours': 7.5, 'sleep_hours': 6.2, 'stress_level': 6, 'grade': 74, 'attendance_rate': 0.90, 'missed_deadline_observed': 0},
    ]


def _overloaded_history(current_day: int) -> List[Dict[str, Any]]:
    """OVERLOADED STUDENT: Low study consistency, severe sleep deficit, high stress, missed deadlines."""
    base_day = max(1, current_day - 6)
    return [
        {'day': base_day + 0, 'study_hours': 2.1, 'sleep_hours': 4.8, 'stress_level': 8, 'grade': 52, 'attendance_rate': 0.68, 'missed_deadline_observed': 1},
        {'day': base_day + 1, 'study_hours': 2.8, 'sleep_hours': 5.1, 'stress_level': 9, 'grade': 50, 'attendance_rate': 0.65, 'missed_deadline_observed': 1},
        {'day': base_day + 2, 'study_hours': 1.9, 'sleep_hours': 4.9, 'stress_level': 9, 'grade': 51, 'attendance_rate': 0.67, 'missed_deadline_observed': 1},
        {'day': base_day + 3, 'study_hours': 2.3, 'sleep_hours': 5.0, 'stress_level': 8, 'grade': 52, 'attendance_rate': 0.70, 'missed_deadline_observed': 1},
        {'day': base_day + 4, 'study_hours': 2.0, 'sleep_hours': 4.7, 'stress_level': 9, 'grade': 50, 'attendance_rate': 0.68, 'missed_deadline_observed': 1},
        {'day': base_day + 5, 'study_hours': 2.6, 'sleep_hours': 5.0, 'stress_level': 9, 'grade': 51, 'attendance_rate': 0.69, 'missed_deadline_observed': 1},
        {'day': current_day, 'study_hours': 2.5, 'sleep_hours': 5.0, 'stress_level': 9, 'grade': 55, 'attendance_rate': 0.70, 'missed_deadline_observed': 1},
    ]


def _recovery_history(current_day: int) -> List[Dict[str, Any]]:
    """RECOVERY PHASE: Improving after stress, better sleep restoration."""
    base_day = max(1, current_day - 6)
    return [
        {'day': base_day + 0, 'study_hours': 3.5, 'sleep_hours': 8.3, 'stress_level': 4, 'grade': 70, 'attendance_rate': 0.86, 'missed_deadline_observed': 0},
        {'day': base_day + 1, 'study_hours': 3.8, 'sleep_hours': 8.4, 'stress_level': 4, 'grade': 71, 'attendance_rate': 0.87, 'missed_deadline_observed': 0},
        {'day': base_day + 2, 'study_hours': 4.0, 'sleep_hours': 8.2, 'stress_level': 3, 'grade': 71, 'attendance_rate': 0.88, 'missed_deadline_observed': 0},
        {'day': base_day + 3, 'study_hours': 4.1, 'sleep_hours': 8.1, 'stress_level': 3, 'grade': 72, 'attendance_rate': 0.89, 'missed_deadline_observed': 0},
        {'day': base_day + 4, 'study_hours': 3.9, 'sleep_hours': 8.3, 'stress_level': 4, 'grade': 71, 'attendance_rate': 0.87, 'missed_deadline_observed': 0},
        {'day': base_day + 5, 'study_hours': 4.0, 'sleep_hours': 8.2, 'stress_level': 3, 'grade': 72, 'attendance_rate': 0.88, 'missed_deadline_observed': 0},
        {'day': current_day, 'study_hours': 4.0, 'sleep_hours': 8.2, 'stress_level': 4, 'grade': 72, 'attendance_rate': 0.88, 'missed_deadline_observed': 0},
    ]


def _deadline_history(current_day: int) -> List[Dict[str, Any]]:
    """DEADLINE CRUNCH: Heavy workload near exam period, elevated stress."""
    base_day = max(1, current_day - 6)
    return [
        {'day': base_day + 0, 'study_hours': 5.8, 'sleep_hours': 5.9, 'stress_level': 7, 'grade': 77, 'attendance_rate': 0.85, 'missed_deadline_observed': 0},
        {'day': base_day + 1, 'study_hours': 6.2, 'sleep_hours': 5.7, 'stress_level': 7, 'grade': 77, 'attendance_rate': 0.84, 'missed_deadline_observed': 0},
        {'day': base_day + 2, 'study_hours': 6.0, 'sleep_hours': 5.8, 'stress_level': 7, 'grade': 77, 'attendance_rate': 0.86, 'missed_deadline_observed': 1},
        {'day': base_day + 3, 'study_hours': 6.1, 'sleep_hours': 5.9, 'stress_level': 8, 'grade': 78, 'attendance_rate': 0.85, 'missed_deadline_observed': 0},
        {'day': base_day + 4, 'study_hours': 5.9, 'sleep_hours': 5.8, 'stress_level': 7, 'grade': 77, 'attendance_rate': 0.84, 'missed_deadline_observed': 1},
        {'day': base_day + 5, 'study_hours': 6.0, 'sleep_hours': 5.9, 'stress_level': 8, 'grade': 78, 'attendance_rate': 0.85, 'missed_deadline_observed': 0},
        {'day': current_day, 'study_hours': 6.0, 'sleep_hours': 5.8, 'stress_level': 8, 'grade': 78, 'attendance_rate': 0.85, 'missed_deadline_observed': 1},
    ]
