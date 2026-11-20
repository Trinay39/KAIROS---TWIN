"""
KAIROS-TWIN Phase 3: Integration Pipeline.

Orchestrates the entire Phase 3 pipeline:
1. Load Phase 2 synthetic data
2. Compute StudentTwinState for each student-day
3. Extract 46 features
4. Compute 5-criterion labels
5. Create temporal samples
6. Run leakage detection tests
7. Generate Phase 3 dataset
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import pickle
import json

from core.schemas import StudentTwinState
from core.twin_engine import TwinEngine
from core.feature_engine import FeatureEngine
from core.label_engine import LabelEngine
from core.temporal_sampler import TemporalSampler, Sample
from core.leakage_tests import LeakageTests


class Phase3Pipeline:
    """Orchestrates Phase 3: Twin State, Features, Labels, Temporal Sampling."""

    def __init__(
        self,
        phase2_csv: str = "data/synthetic_student_daily.csv",
        baseline_sleep: float = 7.5
    ):
        """
        Initialize Phase 3 pipeline.

        Args:
            phase2_csv: Path to Phase 2 synthetic data
            baseline_sleep: Recovery baseline (hours)
        """
        self.phase2_csv = phase2_csv
        self.baseline_sleep = baseline_sleep

        # Initialize engines
        self.twin_engine = TwinEngine(baseline_sleep=baseline_sleep)
        self.feature_engine = FeatureEngine()
        self.label_engine = LabelEngine()
        self.sampler = TemporalSampler()
        self.leakage_tester = LeakageTests()

        # Load data
        print("Loading Phase 2 synthetic data...")
        self.df_all = pd.read_csv(phase2_csv)
        print(f"[OK] Loaded {len(self.df_all):,} observations")

    def run(self) -> Dict[str, any]:
        """
        Run full Phase 3 pipeline.

        Returns:
            Dict with results and statistics
        """
        print("\n" + "=" * 70)
        print("PHASE 3: TWIN STATE, FEATURES, LABELS, TEMPORAL SAMPLING")
        print("=" * 70)

        # Step 1: Compute twin states
        print("\n[Step 1/7] Computing StudentTwinState for each student-day...")
        twin_states_by_day = self._compute_twin_states()
        print(f"[OK] Computed {len(twin_states_by_day):,} twin states")

        # Step 2: Extract features
        print("\n[Step 2/7] Extracting 46 features from twin states...")
        features_by_day = self._extract_features(twin_states_by_day)
        print(f"[OK] Extracted features for {len(features_by_day):,} states")

        # Step 3: Compute labels
        print("\n[Step 3/7] Computing 5-criterion overload labels...")
        labels_by_day = self._compute_labels()
        print(f"[OK] Computed labels for {len(labels_by_day):,} states")

        # Step 4: Create temporal samples
        print("\n[Step 4/7] Creating temporal samples...")
        students = sorted(self.df_all['student_id'].unique())
        train_samples, val_samples, test_samples = self.sampler.create_temporal_samples(
            features_by_day, labels_by_day, students
        )
        print(f"[OK] Train: {len(train_samples):,} | Val: {len(val_samples):,} | Test: {len(test_samples):,}")

        # Step 5: Run leakage tests
        print("\n[Step 5/7] Running leakage detection tests...")
        leakage_results = self.leakage_tester.run_all_tests(
            train_samples, val_samples, test_samples
        )
        self.leakage_tester.print_results(leakage_results)

        # Step 6: Convert to dataframes
        print("\n[Step 6/7] Converting samples to dataframes...")
        df_train = self.sampler.to_dataframe(train_samples)
        df_val = self.sampler.to_dataframe(val_samples)
        df_test = self.sampler.to_dataframe(test_samples)
        print(f"[OK] Train: {df_train.shape} | Val: {df_val.shape} | Test: {df_test.shape}")

        # Step 7: Save outputs
        print("\n[Step 7/7] Saving Phase 3 outputs...")
        output_dir = Path("data/phase3")
        output_dir.mkdir(exist_ok=True)

        df_train.to_csv(output_dir / "train.csv", index=False)
        df_val.to_csv(output_dir / "val.csv", index=False)
        df_test.to_csv(output_dir / "test.csv", index=False)

        # Save combined dataset
        df_combined = pd.concat([df_train, df_val, df_test], ignore_index=True)
        df_combined.to_csv(output_dir / "combined.csv", index=False)

        print(f"[OK] Saved to {output_dir}/")

        # Generate report
        report = self._generate_report(
            train_samples, val_samples, test_samples,
            df_train, df_val, df_test,
            leakage_results
        )

        return {
            'train_samples': train_samples,
            'val_samples': val_samples,
            'test_samples': test_samples,
            'df_train': df_train,
            'df_val': df_val,
            'df_test': df_test,
            'leakage_results': leakage_results,
            'report': report,
        }

    def _compute_twin_states(self) -> Dict[Tuple[str, int], StudentTwinState]:
        """Compute StudentTwinState for each student-day."""
        twin_states = {}

        students = sorted(self.df_all['student_id'].unique())
        total = len(students) * 90

        for i, student_id in enumerate(students):
            student_df = self.df_all[self.df_all['student_id'] == student_id].copy()

            for day in range(1, 91):
                obs_up_to_t = student_df[student_df['day'] <= day]

                try:
                    state = self.twin_engine.compute_state(
                        student_id, day, obs_up_to_t, data_source='synthetic'
                    )
                    twin_states[(student_id, day)] = state
                except Exception as e:
                    print(f"[WARN] Error computing state for student {student_id}, day {day}: {e}")

            if (i + 1) % 50 == 0:
                print(f"  Progress: {i + 1}/{len(students)} students")

        return twin_states

    def _extract_features(
        self,
        twin_states: Dict[Tuple[str, int], StudentTwinState]
    ) -> Dict[Tuple[str, int], Dict[str, float]]:
        """Extract 46 features from each twin state."""
        features = {}

        for (student_id, day), state in twin_states.items():
            try:
                feature_vector = self.feature_engine.extract_features(state)
                features[(student_id, day)] = feature_vector
            except Exception as e:
                print(f"⚠ Error extracting features for student {student_id}, day {day}: {e}")

        return features

    def _compute_labels(self) -> Dict[Tuple[str, int], Dict[str, any]]:
        """Compute labels for each student-day."""
        labels = {}

        students = sorted(self.df_all['student_id'].unique())

        for i, student_id in enumerate(students):
            student_df = self.df_all[self.df_all['student_id'] == student_id].copy()

            for day in range(1, 84):  # [1, 83]; labels computed from [t+1, t+7]
                outcome_window = student_df[
                    (student_df['day'] > day) & (student_df['day'] <= day + 7)
                ]

                if len(outcome_window) < 3:
                    continue

                try:
                    # Compute baseline for this student
                    hist_up_to_t = student_df[student_df['day'] <= day]
                    baseline_study_30d = hist_up_to_t['study_hours'].tail(30).mean()
                    baseline_grade = hist_up_to_t['grade'].dropna().tail(5).mean()

                    label_dict = self.label_engine.compute_labels(
                        student_id, day, outcome_window,
                        baseline_study_30d=baseline_study_30d,
                        baseline_grade=baseline_grade
                    )
                    labels[(student_id, day)] = label_dict
                except Exception as e:
                    pass  # Some labels will be unknown; that's OK

            if (i + 1) % 50 == 0:
                print(f"  Progress: {i + 1}/{len(students)} students")

        return labels

    def _generate_report(
        self,
        train_samples: List[Sample],
        val_samples: List[Sample],
        test_samples: List[Sample],
        df_train: pd.DataFrame,
        df_val: pd.DataFrame,
        df_test: pd.DataFrame,
        leakage_results: Dict
    ) -> Dict[str, any]:
        """Generate summary statistics report."""
        all_samples = train_samples + val_samples + test_samples

        # Label statistics
        all_y_binary = [s.y_binary for s in all_samples]
        overload_count = sum(1 for y in all_y_binary if y)
        base_rate = overload_count / len(all_y_binary) if all_y_binary else 0

        # Criteria statistics
        criteria_counts = {
            'C1_missed_deadline': sum(1 for s in all_samples if s.criteria and s.criteria.get('C1_missed_deadline') is True),
            'C2_grade_deterioration': sum(1 for s in all_samples if s.criteria and s.criteria.get('C2_grade_deterioration') is True),
            'C3_study_collapse': sum(1 for s in all_samples if s.criteria and s.criteria.get('C3_study_collapse') is True),
            'C4_recovery_failure': sum(1 for s in all_samples if s.criteria and s.criteria.get('C4_recovery_failure') is True),
            'C5_high_stress': sum(1 for s in all_samples if s.criteria and s.criteria.get('C5_high_stress') is True),
        }

        # Feature statistics
        feature_cols = [c for c in df_train.columns if c.startswith('X_')]

        report = {
            'phase': 'Phase 3',
            'timestamp': pd.Timestamp.now().isoformat(),
            'samples': {
                'train': len(train_samples),
                'val': len(val_samples),
                'test': len(test_samples),
                'total': len(all_samples),
            },
            'labels': {
                'base_rate': base_rate,
                'base_rate_pct': 100 * base_rate,
                'overload_count': overload_count,
                'not_overload_count': len(all_y_binary) - overload_count,
            },
            'criteria': criteria_counts,
            'features': {
                'count': len(feature_cols),
                'names': sorted([c.replace('X_', '') for c in feature_cols]),
            },
            'leakage_tests': {
                'all_passed': leakage_results['all_passed'],
                'tests': {k: v.get('passed', False) for k, v in leakage_results['tests'].items()},
            },
        }

        return report


def main():
    """Run Phase 3 pipeline."""
    pipeline = Phase3Pipeline(
        phase2_csv="data/synthetic_student_daily.csv",
        baseline_sleep=7.5
    )

    results = pipeline.run()

    # Print final report
    print("\n" + "=" * 70)
    print("PHASE 3 SUMMARY REPORT")
    print("=" * 70)

    report = results['report']
    print(f"\nSamples:")
    print(f"  Train: {report['samples']['train']:,}")
    print(f"  Val:   {report['samples']['val']:,}")
    print(f"  Test:  {report['samples']['test']:,}")
    print(f"  Total: {report['samples']['total']:,}")

    print(f"\nLabels:")
    print(f"  Overload base rate: {report['labels']['base_rate_pct']:.1f}%")
    print(f"  Overload count: {report['labels']['overload_count']:,}")

    print(f"\nCriteria triggered (across all samples):")
    for cname, count in report['criteria'].items():
        pct = 100 * count / report['samples']['total'] if report['samples']['total'] > 0 else 0
        print(f"  {cname}: {count:,} ({pct:.1f}%)")

    print(f"\nFeatures:")
    print(f"  Total: {report['features']['count']}")

    print(f"\nLeakage Tests:")
    print(f"  All Passed: {report['leakage_tests']['all_passed']}")
    for tname, passed in report['leakage_tests']['tests'].items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"    {status} {tname}")

    print("\n" + "=" * 70)
    print("Phase 3 pipeline complete!")
    print("=" * 70 + "\n")

    return results


if __name__ == '__main__':
    main()
