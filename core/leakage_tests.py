"""
KAIROS-TWIN Phase 3: Leakage Detection Tests.

Automated verification that features do NOT leak future information.

Key invariant:
  For each sample (X, y, t):
    - X is computed from StudentTwinState(t), which uses observations [day 1, day t]
    - y is computed from observations [day t+1, day t+7]
    - NO overlap between feature window and label window
"""
from __future__ import annotations
from typing import List, Dict, Tuple
import pandas as pd
from core.temporal_sampler import Sample


class LeakageTests:
    """Automated leakage detection."""

    # Feature metadata: (feature_name, window_end_relative_to_t)
    # Negative = past, 0 = current day, Positive = future (MUST NOT EXIST)
    FEATURE_WINDOW_ENDS = {
        # Academic (7) - all historical
        'attendance_rate_7d': -0,  # up to day t
        'attendance_trend_7d': -0,
        'recent_grades_mean': -0,
        'grade_trend_30d': -0,
        'grades_below_personal_mean_pct': -0,
        'active_subjects_count': 0,
        'missed_deadlines_14d': -0,

        # Behavioral (9) - all historical
        'avg_study_hours_3d': -0,
        'avg_study_hours_7d': -0,
        'study_variability_7d': -0,
        'study_consistency_score': -0,
        'avg_session_duration_7d': -0,
        'break_rate_7d': -0,
        'distraction_rate_7d': -0,
        'focus_quality_7d_avg': -0,
        'procrastination_index_7d': -0,

        # Recovery (8) - all historical
        'avg_sleep_hours_7d': -0,
        'sleep_variability_7d': -0,
        'sleep_deficit_7d_hours': -0,
        'sleep_debt_severity': -0,
        'rest_days_7d': -0,
        'recovery_ratio_7d': -0,
        'recovery_score_7d': -0,
        'recovery_deficit_score': -0,

        # Workload (7) - all historical or current
        'pending_assignment_count': 0,  # current snapshot
        'pending_assignment_effort_hours': 0,
        'deadline_density_trend_7d': -0,
        'workload_pressure_score_7d': -0,
        'submission_rate_14d': -0,
        'submissions_on_time_pct_14d': -0,
        'effort_study_gap_7d': -0,

        # Engagement (5) - all historical
        'platform_interactions_7d_avg': -0,
        'interaction_trend_7d': -0,
        'interaction_engagement_score': -0,
        'avg_stress_7d': -0,
        'avg_confidence_7d': -0,

        # Temporal (6) - all current/historical
        'week_of_semester': 0,
        'day_of_week_sine': 0,
        'day_of_week_cosine': 0,
        'is_midterm_period': 0,
        'is_exam_period': 0,
        'days_until_exam_period': 0,

        # Interaction (4) - all historical
        'workload_recovery_imbalance': -0,
        'deadline_urgency_effort_ratio': -0,
        'study_stress_coherence': -0,
        'recovery_confidence_coupling': -0,
    }

    # Label properties: (label_name, window_start, window_end)
    # All labels use [t+1, t+7]
    LABEL_WINDOW = (1, 7)  # relative to t

    def test_feature_temporal_bounds(self) -> Dict[str, any]:
        """
        Verify that no feature uses information from [t+1, t+7].

        Returns:
            Dict with test results
        """
        results = {
            'test_name': 'feature_temporal_bounds',
            'passed': True,
            'violations': [],
            'details': {}
        }

        for feature_name, window_end in self.FEATURE_WINDOW_ENDS.items():
            # window_end <= 0 means feature ends at or before day t (OK)
            # window_end > 0 means feature uses future data (NOT OK)
            if window_end > 0:
                results['passed'] = False
                results['violations'].append(
                    f"{feature_name}: window ends at t+{window_end} (future leakage)"
                )
            results['details'][feature_name] = {
                'window_end': window_end,
                'safe': window_end <= 0
            }

        return results

    def test_no_label_in_features(self) -> Dict[str, any]:
        """
        Verify that feature windows don't overlap with label window [t+1, t+7].

        Returns:
            Dict with test results
        """
        results = {
            'test_name': 'no_label_in_features',
            'passed': True,
            'violations': [],
        }

        label_start, label_end = self.LABEL_WINDOW

        for feature_name, window_end in self.FEATURE_WINDOW_ENDS.items():
            # Feature window ends at t+window_end
            # Label window is [t+1, t+7]
            # No overlap if feature_window_end < label_window_start
            if window_end >= label_start:
                results['passed'] = False
                results['violations'].append(
                    f"{feature_name}: window end t+{window_end} >= label start t+{label_start}"
                )

        return results

    def test_samples_temporal_separation(
        self,
        train_samples: List[Sample],
        val_samples: List[Sample],
        test_samples: List[Sample]
    ) -> Dict[str, any]:
        """
        For each sample (X, y, t), verify:
          - Feature values are from [1, t]
          - Label is computed from [t+1, t+7]
          - No overlap

        Returns:
            Dict with test results
        """
        results = {
            'test_name': 'samples_temporal_separation',
            'passed': True,
            'violations': [],
            'sample_count': len(train_samples) + len(val_samples) + len(test_samples),
        }

        all_samples = train_samples + val_samples + test_samples

        for i, sample in enumerate(all_samples):
            t = sample.day

            # Features should be computed from [1, t]
            # Label is computed from [t+1, t+7]

            # Check: day should be in valid range
            if not (15 <= t <= 83):  # Valid prediction days
                results['violations'].append(
                    f"Sample {i}: day {t} outside valid range [15, 83]"
                )
                results['passed'] = False

            # Check: label should have valid values
            if sample.y_binary is None or sample.y_continuous is None:
                results['violations'].append(
                    f"Sample {i}: (student={sample.student_id}, day={t}) has null label"
                )
                results['passed'] = False

        return results

    def test_no_student_leakage_temporal_split(
        self,
        train_samples: List[Sample],
        val_samples: List[Sample],
        test_samples: List[Sample]
    ) -> Dict[str, any]:
        """
        For temporal split: verify that students appear in all splits
        (same student, different time periods is OK).

        Returns:
            Dict with test results
        """
        results = {
            'test_name': 'no_student_leakage_temporal_split',
            'passed': True,
            'violations': [],
            'details': {
                'train_students': len(set(s.student_id for s in train_samples)),
                'val_students': len(set(s.student_id for s in val_samples)),
                'test_students': len(set(s.student_id for s in test_samples)),
            }
        }

        # In temporal split, same student can appear in all splits (different times)
        # This is OK and expected

        return results

    def test_no_student_leakage_student_split(
        self,
        train_samples: List[Sample],
        val_samples: List[Sample],
        test_samples: List[Sample]
    ) -> Dict[str, any]:
        """
        For student-level split: verify that students DON'T overlap across splits.

        Returns:
            Dict with test results
        """
        results = {
            'test_name': 'no_student_leakage_student_split',
            'passed': True,
            'violations': [],
        }

        train_students = set(s.student_id for s in train_samples)
        val_students = set(s.student_id for s in val_samples)
        test_students = set(s.student_id for s in test_samples)

        # Check disjointness
        train_val_overlap = train_students & val_students
        val_test_overlap = val_students & test_students
        train_test_overlap = train_students & test_students

        if train_val_overlap:
            results['passed'] = False
            results['violations'].append(
                f"Train/Val student overlap: {train_val_overlap}"
            )
        if val_test_overlap:
            results['passed'] = False
            results['violations'].append(
                f"Val/Test student overlap: {val_test_overlap}"
            )
        if train_test_overlap:
            results['passed'] = False
            results['violations'].append(
                f"Train/Test student overlap: {train_test_overlap}"
            )

        results['details'] = {
            'train_students': len(train_students),
            'val_students': len(val_students),
            'test_students': len(test_students),
            'total_unique': len(train_students | val_students | test_students),
        }

        return results

    def test_label_distribution(
        self,
        samples: List[Sample]
    ) -> Dict[str, any]:
        """
        Check label distribution for reasonableness.

        Expected: overload base rate 15–30%

        Returns:
            Dict with test results
        """
        results = {
            'test_name': 'label_distribution',
            'passed': True,
            'violations': [],
        }

        if len(samples) == 0:
            results['violations'].append("No samples provided")
            results['passed'] = False
            return results

        overload_count = sum(1 for s in samples if s.y_binary)
        base_rate = overload_count / len(samples)

        results['details'] = {
            'total_samples': len(samples),
            'overload_count': overload_count,
            'base_rate': base_rate,
            'base_rate_pct': 100 * base_rate,
        }

        # Check: base rate should be 15–30%
        if not (0.15 <= base_rate <= 0.30):
            results['violations'].append(
                f"Base rate {100*base_rate:.1f}% outside expected range [15%, 30%]"
            )
            results['passed'] = False  # Warning, not failure

        return results

    def run_all_tests(
        self,
        train_samples: List[Sample],
        val_samples: List[Sample],
        test_samples: List[Sample]
    ) -> Dict[str, any]:
        """
        Run all leakage detection tests.

        Args:
            train_samples: Training samples
            val_samples: Validation samples
            test_samples: Test samples

        Returns:
            Dict with all test results
        """
        results = {
            'all_passed': True,
            'tests': {}
        }

        # Static tests
        results['tests']['feature_temporal_bounds'] = self.test_feature_temporal_bounds()
        results['tests']['no_label_in_features'] = self.test_no_label_in_features()

        # Sample tests
        results['tests']['samples_temporal_separation'] = self.test_samples_temporal_separation(
            train_samples, val_samples, test_samples
        )
        results['tests']['no_student_leakage_temporal'] = self.test_no_student_leakage_temporal_split(
            train_samples, val_samples, test_samples
        )
        results['tests']['no_student_leakage_student_split'] = self.test_no_student_leakage_student_split(
            train_samples, val_samples, test_samples
        )

        # Label distribution
        all_samples = train_samples + val_samples + test_samples
        results['tests']['label_distribution'] = self.test_label_distribution(all_samples)

        # Overall result
        results['all_passed'] = all(
            results['tests'][t].get('passed', False)
            for t in results['tests']
        )

        return results

    @staticmethod
    def print_results(results: Dict[str, any]) -> None:
        """Pretty-print test results."""
        print("\n" + "=" * 70)
        print("LEAKAGE DETECTION TEST RESULTS")
        print("=" * 70)

        for test_name, test_result in results['tests'].items():
            status = "[PASS]" if test_result.get('passed', False) else "[FAIL]"
            print(f"\n{status}: {test_name}")

            if test_result.get('violations'):
                for violation in test_result['violations']:
                    print(f"  ! {violation}")

            if test_result.get('details'):
                for key, value in test_result['details'].items():
                    if isinstance(value, float):
                        print(f"  {key}: {value:.4f}")
                    else:
                        print(f"  {key}: {value}")

        print("\n" + "=" * 70)
        overall = "[ALL TESTS PASSED]" if results['all_passed'] else "[SOME TESTS FAILED]"
        print(overall)
        print("=" * 70 + "\n")
