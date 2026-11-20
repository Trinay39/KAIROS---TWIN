"""
KAIROS-TWIN Phase 3: Temporal Sampler.

Creates train/val/test splits with explicit temporal and student-level separation.

Temporal split (primary evaluation):
- Warm-up: days 1–14 (no predictions; building history)
- Train: days 15–55 (41 samples per student)
- Validation: days 56–69 (14 samples per student)
- Test: days 70–83 (14 samples per student)
- Outcome-only: days 84–90 (compute labels, no predictions)

Student split (secondary evaluation):
- 160 students → training
- 20 students → validation
- 20 students → test

Each (X, y, t) sample:
  X: features from StudentTwinState(t) where t ∈ [15, 83]
  y: overload label computed from outcome window [t+1, t+7]
  t: time (day of semester)
"""
from __future__ import annotations
from typing import List, Tuple, Dict
import pandas as pd
import numpy as np
from dataclasses import dataclass


@dataclass
class Sample:
    """A single training/validation/test sample."""
    student_id: str
    day: int
    X: Dict[str, float]  # 46 features
    y_binary: bool  # primary target
    y_continuous: float  # strain index
    split: str  # "train", "val", or "test"
    criteria: Dict[str, any] = None  # 5-criterion breakdown


class TemporalSampler:
    """Creates temporally-valid train/val/test splits."""

    # Phase boundaries
    WARM_UP_END = 14  # days 1–14
    TRAIN_START = 15
    TRAIN_END = 55  # 41 samples
    VAL_START = 56
    VAL_END = 69  # 14 samples
    TEST_START = 70
    TEST_END = 83  # 14 samples
    SEMESTER_END = 90

    def __init__(self):
        """Initialize sampler."""
        pass

    def get_prediction_days(self) -> Tuple[List[int], List[int], List[int]]:
        """
        Get valid prediction days for each split.

        Returns:
            (train_days, val_days, test_days)
        """
        train_days = list(range(self.TRAIN_START, self.TRAIN_END + 1))
        val_days = list(range(self.VAL_START, self.VAL_END + 1))
        test_days = list(range(self.TEST_START, self.TEST_END + 1))

        return train_days, val_days, test_days

    def create_temporal_samples(
        self,
        features_by_day: Dict[Tuple[str, int], Dict[str, float]],
        labels_by_day: Dict[Tuple[str, int], Dict[str, any]],
        students: List[str]
    ) -> Tuple[List[Sample], List[Sample], List[Sample]]:
        """
        Create train/val/test samples using temporal split.

        Args:
            features_by_day: {(student_id, day): {feature_name: value}}
            labels_by_day: {(student_id, day): {C1, C2, ...}}
            students: List of student IDs

        Returns:
            (train_samples, val_samples, test_samples)
        """
        train_days, val_days, test_days = self.get_prediction_days()

        train_samples = []
        val_samples = []
        test_samples = []

        for student_id in students:
            # Train samples
            for day in train_days:
                sample = self._create_sample(
                    student_id, day, features_by_day, labels_by_day, split="train"
                )
                if sample:
                    train_samples.append(sample)

            # Validation samples
            for day in val_days:
                sample = self._create_sample(
                    student_id, day, features_by_day, labels_by_day, split="val"
                )
                if sample:
                    val_samples.append(sample)

            # Test samples
            for day in test_days:
                sample = self._create_sample(
                    student_id, day, features_by_day, labels_by_day, split="test"
                )
                if sample:
                    test_samples.append(sample)

        return train_samples, val_samples, test_samples

    def create_student_level_split(
        self,
        all_samples: List[Sample],
        train_frac: float = 0.8,
        val_frac: float = 0.1,
        test_frac: float = 0.1,
        seed: int = 42
    ) -> Tuple[List[Sample], List[Sample], List[Sample]]:
        """
        Create student-level split (secondary evaluation).

        Args:
            all_samples: All samples
            train_frac: Fraction of students for training
            val_frac: Fraction for validation
            test_frac: Fraction for test
            seed: Random seed

        Returns:
            (train_samples, val_samples, test_samples)
        """
        np.random.seed(seed)

        # Get unique students
        students = sorted(set(s.student_id for s in all_samples))
        n_students = len(students)

        # Shuffle and split
        shuffled = np.random.permutation(students)
        n_train = int(n_students * train_frac)
        n_val = int(n_students * val_frac)

        train_students = set(shuffled[:n_train])
        val_students = set(shuffled[n_train:n_train + n_val])
        test_students = set(shuffled[n_train + n_val:])

        train_samples = [s for s in all_samples if s.student_id in train_students]
        val_samples = [s for s in all_samples if s.student_id in val_students]
        test_samples = [s for s in all_samples if s.student_id in test_students]

        return train_samples, val_samples, test_samples

    def to_dataframe(self, samples: List[Sample]) -> pd.DataFrame:
        """
        Convert samples to DataFrame.

        Args:
            samples: List of Sample objects

        Returns:
            DataFrame with columns: student_id, day, X_*, y_binary, y_continuous, split
        """
        rows = []
        for sample in samples:
            row = {
                'student_id': sample.student_id,
                'day': sample.day,
                'y_binary': sample.y_binary,
                'y_continuous': sample.y_continuous,
                'split': sample.split,
            }
            # Add all features with X_ prefix
            for fname, fvalue in sample.X.items():
                row[f'X_{fname}'] = fvalue

            # Add criteria if available
            if sample.criteria:
                for cname, cvalue in sample.criteria.items():
                    row[f'C_{cname}'] = cvalue

            rows.append(row)

        return pd.DataFrame(rows)

    def verify_temporal_separation(
        self,
        train_samples: List[Sample],
        val_samples: List[Sample],
        test_samples: List[Sample]
    ) -> Dict[str, bool]:
        """
        Verify no temporal leakage between splits.

        Args:
            train_samples: Training samples
            val_samples: Validation samples
            test_samples: Test samples

        Returns:
            Dict of checks: {check_name: passed (bool)}
        """
        checks = {}

        # Extract day ranges
        train_days = set(s.day for s in train_samples)
        val_days = set(s.day for s in val_samples)
        test_days = set(s.day for s in test_samples)

        # Check no overlap
        checks['no_train_val_overlap'] = len(train_days & val_days) == 0
        checks['no_val_test_overlap'] = len(val_days & test_days) == 0
        checks['no_train_test_overlap'] = len(train_days & test_days) == 0

        # Check ordering
        checks['train_before_val'] = max(train_days or [0]) < min(val_days or [999])
        checks['val_before_test'] = max(val_days or [0]) < min(test_days or [999])

        return checks

    def verify_student_separation(
        self,
        train_samples: List[Sample],
        val_samples: List[Sample],
        test_samples: List[Sample]
    ) -> Dict[str, bool]:
        """
        Verify no student overlap in student-level split.

        Args:
            train_samples: Training samples
            val_samples: Validation samples
            test_samples: Test samples

        Returns:
            Dict of checks: {check_name: passed (bool)}
        """
        checks = {}

        train_students = set(s.student_id for s in train_samples)
        val_students = set(s.student_id for s in val_samples)
        test_students = set(s.student_id for s in test_samples)

        checks['no_train_val_students'] = len(train_students & val_students) == 0
        checks['no_val_test_students'] = len(val_students & test_students) == 0
        checks['no_train_test_students'] = len(train_students & test_students) == 0

        return checks

    @staticmethod
    def _create_sample(
        student_id: str,
        day: int,
        features_by_day: Dict,
        labels_by_day: Dict,
        split: str
    ) -> Sample:
        """
        Create a single (X, y, t) sample.

        Args:
            student_id: Student ID
            day: Day of semester
            features_by_day: Dict of features
            labels_by_day: Dict of labels
            split: "train", "val", or "test"

        Returns:
            Sample object, or None if missing data
        """
        key = (student_id, day)

        # Check if features and labels exist
        if key not in features_by_day or key not in labels_by_day:
            return None

        features = features_by_day[key]
        labels = labels_by_day[key]

        # Check if label is valid (not unknown)
        if labels.get('criteria_unknown', False):
            return None

        return Sample(
            student_id=student_id,
            day=day,
            X=features,
            y_binary=bool(labels.get('overload_binary', False)),
            y_continuous=float(labels.get('strain_index', 0.0)),
            split=split,
            criteria={
                'C1_missed_deadline': labels.get('C1_missed_deadline'),
                'C2_grade_deterioration': labels.get('C2_grade_deterioration'),
                'C3_study_collapse': labels.get('C3_study_collapse'),
                'C4_recovery_failure': labels.get('C4_recovery_failure'),
                'C5_high_stress': labels.get('C5_high_stress'),
                'criteria_triggered': labels.get('criteria_triggered', 0),
            }
        )
