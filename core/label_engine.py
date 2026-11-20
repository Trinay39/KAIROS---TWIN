"""
KAIROS-TWIN Phase 3: Label Engine.

Computes the 5-criterion academic overload label for a 7-day outcome window [t+1, t+7].

Target definition (from Phase 1B):
- Binary: overload_7d = (≥2 of 5 criteria triggered)
- Continuous: strain_index (0-1 weighted average)

Criteria:
  C1: Missed deadline — ≥1 assignment due during [t+1, t+7] was not submitted
  C2: Grade deterioration — grade drop ≥15pp from personal baseline
  C3: Study collapse — mean study [t+1, t+7] < 50% of 30-day baseline
  C4: Recovery failure — mean sleep < 5.5 hours AND deficit > 10 hours
  C5: High stress — mean stress ≥4.0 (on 1-5 Likert)

Key principle: Labels use FUTURE outcomes [t+1, t+7], never current features.
"""
from __future__ import annotations
from typing import Dict, Tuple, Optional
import numpy as np
import pandas as pd


class LabelEngine:
    """Computes overload labels from future observations."""

    # Configuration
    GRADE_DROP_THRESHOLD = 0.15  # 15 percentage points
    STUDY_COLLAPSE_THRESHOLD = 0.50  # 50% of baseline
    SLEEP_MINIMUM = 5.5  # hours
    SLEEP_DEFICIT_THRESHOLD = 10  # cumulative hours
    STRESS_THRESHOLD = 4.0  # on 1-5 Likert scale
    STRESS_RAW_THRESHOLD = 0.65  # on 0.1-1.0 simulator scale (~2.6 Likert)
    BASELINE_SLEEP = 7.5  # default for deficit calculation

    def compute_labels(
        self,
        student_id: str,
        day: int,
        all_obs: pd.DataFrame,
        baseline_study_30d: Optional[float] = None,
        baseline_grade: Optional[float] = None
    ) -> Dict[str, any]:
        """
        Compute overload labels for outcome window [day+1, day+7].

        Args:
            student_id: Student identifier
            day: Day of semester (t) [1, 90]
            all_obs: All observations for this student (filtered to [day+1, day+7] for outcomes)
            baseline_study_30d: Optional pre-computed 30-day study baseline
            baseline_grade: Optional pre-computed personal grade baseline

        Returns:
            Dict containing:
            {
                'C1_missed_deadline': bool,
                'C2_grade_deterioration': bool,
                'C3_study_collapse': bool,
                'C4_recovery_failure': bool,
                'C5_high_stress': bool,
                'criteria_triggered': int,
                'overload_binary': bool,
                'strain_index': float,
            }
        """
        # Extract outcome window [t+1, t+7]
        outcome_window = all_obs[
            (all_obs['day'] > day) & (all_obs['day'] <= day + 7)
        ]

        if len(outcome_window) == 0:
            # No future observations; label is unknown
            return {
                'C1_missed_deadline': None,
                'C2_grade_deterioration': None,
                'C3_study_collapse': None,
                'C4_recovery_failure': None,
                'C5_high_stress': None,
                'criteria_triggered': 0,
                'overload_binary': None,
                'strain_index': None,
                'criteria_unknown': True,
            }

        # Compute each criterion
        C1 = self._check_criterion_1_missed_deadline(outcome_window)
        C2 = self._check_criterion_2_grade_deterioration(
            outcome_window, baseline_grade
        )
        C3 = self._check_criterion_3_study_collapse(
            outcome_window, baseline_study_30d
        )
        C4 = self._check_criterion_4_recovery_failure(outcome_window)
        C5 = self._check_criterion_5_high_stress(outcome_window)

        # Count triggered criteria (excluding None)
        criteria_list = [C1, C2, C3, C4, C5]
        triggered = sum(1 for c in criteria_list if c is True)
        unknown_count = sum(1 for c in criteria_list if c is None)

        # Binary label: ≥2 criteria triggered
        overload_binary = triggered >= 2

        # Continuous strain index
        strain_index = self._compute_strain_index(
            outcome_window, baseline_study_30d, baseline_grade
        )

        return {
            'C1_missed_deadline': C1,
            'C2_grade_deterioration': C2,
            'C3_study_collapse': C3,
            'C4_recovery_failure': C4,
            'C5_high_stress': C5,
            'criteria_triggered': triggered,
            'criteria_unknown': unknown_count,
            'overload_binary': overload_binary,
            'strain_index': strain_index,
        }

    def _check_criterion_1_missed_deadline(
        self,
        outcome_window: pd.DataFrame
    ) -> Optional[bool]:
        """
        C1: Missed deadline — ≥1 assignment due during outcome window not submitted.

        Uses simulator's 'assignment_due_today' and 'missed_deadline_observed'.
        """
        if 'missed_deadline_observed' not in outcome_window.columns:
            return None

        missed_count = outcome_window['missed_deadline_observed'].sum()
        return bool(missed_count >= 1)

    def _check_criterion_2_grade_deterioration(
        self,
        outcome_window: pd.DataFrame,
        baseline_grade: Optional[float] = None
    ) -> Optional[bool]:
        """
        C2: Grade deterioration — grade drop ≥15pp from personal baseline.

        Requires grades in outcome window and knowledge of personal baseline.
        """
        if 'grade' not in outcome_window.columns:
            return None

        outcome_grades = outcome_window['grade'].dropna()
        if len(outcome_grades) == 0:
            return None

        # If baseline not provided, use cohort default
        if baseline_grade is None:
            baseline_grade = 66.3  # Phase 2 mean

        worst_grade = outcome_grades.min()
        # Normalize both to [0, 1]
        worst_normalized = worst_grade / 100.0
        baseline_normalized = baseline_grade / 100.0

        # Drop ≥ 15pp
        drop = (baseline_normalized - worst_normalized) * 100
        return bool(drop >= self.GRADE_DROP_THRESHOLD * 100)

    def _check_criterion_3_study_collapse(
        self,
        outcome_window: pd.DataFrame,
        baseline_study_30d: Optional[float] = None
    ) -> Optional[bool]:
        """
        C3: Study collapse — mean study hours [t+1, t+7] < 50% of baseline.
        """
        if 'study_hours' not in outcome_window.columns:
            return None

        future_study = outcome_window['study_hours'].dropna()
        if len(future_study) < 3:  # Require at least 3 data points
            return None

        future_mean = future_study.mean()

        # If baseline not provided, use Phase 2 mean
        if baseline_study_30d is None:
            baseline_study_30d = 3.7  # Phase 2 mean

        collapse_threshold = self.STUDY_COLLAPSE_THRESHOLD * baseline_study_30d
        return bool(future_mean < collapse_threshold)

    def _check_criterion_4_recovery_failure(
        self,
        outcome_window: pd.DataFrame
    ) -> Optional[bool]:
        """
        C4: Recovery failure — mean sleep < 5.5 hours AND deficit > 10 hours.
        """
        if 'sleep_hours' not in outcome_window.columns:
            return None

        future_sleep = outcome_window['sleep_hours'].dropna()
        if len(future_sleep) < 3:
            return None

        future_mean = future_sleep.mean()
        deficit = (self.BASELINE_SLEEP - future_sleep).clip(lower=0).sum()

        return bool(
            (future_mean < self.SLEEP_MINIMUM) and
            (deficit > self.SLEEP_DEFICIT_THRESHOLD)
        )

    def _check_criterion_5_high_stress(
        self,
        outcome_window: pd.DataFrame
    ) -> Optional[bool]:
        """
        C5: High stress — mean self-reported stress ≥4.0 (on 1-5 Likert).

        In simulator, stress is on [0.1, 1.0]. Map to Likert: Likert = 1 + 4*stress_raw.
        """
        if 'stress_level' not in outcome_window.columns:
            return None

        future_stress = outcome_window['stress_level'].dropna()
        if len(future_stress) < 3:
            return None

        # Convert [0.1, 1.0] to [1, 5] Likert
        future_stress_likert = 1.0 + 4.0 * future_stress
        future_mean = future_stress_likert.mean()

        return bool(future_mean >= self.STRESS_THRESHOLD)

    def _compute_strain_index(
        self,
        outcome_window: pd.DataFrame,
        baseline_study_30d: Optional[float] = None,
        baseline_grade: Optional[float] = None
    ) -> Optional[float]:
        """
        Compute continuous strain index [0, 1] as weighted average of criteria.

        Strain_index = (w1*C1_sev + w2*C2_sev + w3*C3_sev + w4*C4_sev + w5*C5_sev) / 5

        Each component normalized to [0, 1].
        """
        w = 0.2  # equal weighting

        severities = []

        # C1: Missed deadline severity
        if 'missed_deadline_observed' in outcome_window.columns:
            missed_count = outcome_window['missed_deadline_observed'].sum()
            expected_count = max(1, (outcome_window['assignment_due_today'].sum() if 'assignment_due_today' in outcome_window.columns else 1))
            C1_sev = min(1.0, missed_count / expected_count)
        else:
            C1_sev = 0.0
        severities.append(w * C1_sev)

        # C2: Grade drop severity
        if 'grade' in outcome_window.columns:
            outcome_grades = outcome_window['grade'].dropna()
            if len(outcome_grades) > 0:
                if baseline_grade is None:
                    baseline_grade = 66.3
                worst = outcome_grades.min()
                drop_pct = (baseline_grade - worst) / baseline_grade
                C2_sev = min(1.0, drop_pct)
            else:
                C2_sev = 0.0
        else:
            C2_sev = 0.0
        severities.append(w * C2_sev)

        # C3: Study collapse severity
        if 'study_hours' in outcome_window.columns:
            future_study = outcome_window['study_hours'].dropna()
            if len(future_study) > 0:
                if baseline_study_30d is None:
                    baseline_study_30d = 3.7
                future_mean = future_study.mean()
                C3_sev = max(0.0, 1.0 - (future_mean / baseline_study_30d))
                C3_sev = min(1.0, C3_sev)
            else:
                C3_sev = 0.0
        else:
            C3_sev = 0.0
        severities.append(w * C3_sev)

        # C4: Recovery failure severity
        if 'sleep_hours' in outcome_window.columns:
            future_sleep = outcome_window['sleep_hours'].dropna()
            if len(future_sleep) > 0:
                future_mean = future_sleep.mean()
                C4_sev = max(0.0, 1.0 - (future_mean / self.BASELINE_SLEEP))
                C4_sev = min(1.0, C4_sev)
            else:
                C4_sev = 0.0
        else:
            C4_sev = 0.0
        severities.append(w * C4_sev)

        # C5: Stress severity
        if 'stress_level' in outcome_window.columns:
            future_stress = outcome_window['stress_level'].dropna()
            if len(future_stress) > 0:
                future_likert = 1.0 + 4.0 * future_stress.mean()
                C5_sev = (future_likert - 1.0) / 4.0  # normalize to [0, 1]
                C5_sev = min(1.0, C5_sev)
            else:
                C5_sev = 0.0
        else:
            C5_sev = 0.0
        severities.append(w * C5_sev)

        strain_index = sum(severities)
        return float(np.clip(strain_index, 0.0, 1.0))
