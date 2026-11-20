"""
KAIROS-TWIN Phase 4: Data Loader.

Load and validate Phase 3 ML dataset (train/val/test splits).

Schema validation:
- 46 features (X_*)
- 2 targets (y_binary, y_continuous)
- 5 metadata columns
- 6 criteria columns
- Zero NaN values
"""
from __future__ import annotations
from typing import Tuple, List, Dict, Any
from pathlib import Path
import pandas as pd
import numpy as np
from ml.feature_contract import (
    EXPECTED_FEATURE_COUNT,
    FeatureContractError,
    prefixed_feature_order,
    validate_prefixed_feature_columns,
)


class DataLoader:
    """Load and validate Phase 3 ML dataset."""

    REQUIRED_FEATURES = EXPECTED_FEATURE_COUNT
    REQUIRED_METADATA = ['student_id', 'day', 'y_binary', 'y_continuous', 'split']
    FEATURE_PREFIX = 'X_'
    CRITERIA_PREFIX = 'C_'
    VALID_SPLITS = {'train', 'val', 'test'}

    def __init__(
        self,
        train_path: str,
        val_path: str,
        test_path: str,
        verbose: bool = True
    ):
        """
        Initialize data loader.

        Args:
            train_path: Path to train CSV
            val_path: Path to val CSV
            test_path: Path to test CSV
            verbose: Print validation details
        """
        self.train_path = Path(train_path)
        self.val_path = Path(val_path)
        self.test_path = Path(test_path)
        self.verbose = verbose

        self.df_train = None
        self.df_val = None
        self.df_test = None
        self.feature_names = None

    def load(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Load all three splits.

        Returns:
            (df_train, df_val, df_test)
        """
        if self.verbose:
            print("Loading Phase 3 dataset...")

        self.df_train = pd.read_csv(self.train_path)
        self.df_val = pd.read_csv(self.val_path)
        self.df_test = pd.read_csv(self.test_path)

        if self.verbose:
            print(f"  Train: {len(self.df_train):,} samples")
            print(f"  Val: {len(self.df_val):,} samples")
            print(f"  Test: {len(self.df_test):,} samples")

        return self.df_train, self.df_val, self.df_test

    def validate(self) -> Dict[str, Any]:
        """
        Validate dataset schema and integrity.

        Returns:
            Dict with validation results
        """
        if self.df_train is None:
            raise ValueError("Call load() first")

        results = {
            'schema': self._validate_schema(),
            'features': self._validate_features(),
            'targets': self._validate_targets(),
            'missing': self._validate_missing_values(),
            'ranges': self._validate_ranges(),
            'split_consistency': self._validate_split_consistency(),
            'all_passed': True
        }

        # Overall pass/fail
        results['all_passed'] = all(
            v.get('passed', False) if isinstance(v, dict) else True
            for k, v in results.items()
            if k != 'all_passed'
        )

        if self.verbose:
            self._print_validation_results(results)

        return results

    def _validate_schema(self) -> Dict[str, Any]:
        """Verify required columns present."""
        result = {
            'passed': True,
            'issues': [],
        }

        # Check metadata
        for col in self.REQUIRED_METADATA:
            if col not in self.df_train.columns:
                result['issues'].append(f"Missing metadata column: {col}")
                result['passed'] = False

        # Check feature count
        try:
            feature_cols = self._get_feature_columns()
        except FeatureContractError as exc:
            feature_cols = []
            result['issues'].append(str(exc))
            result['passed'] = False
        if len(feature_cols) != self.REQUIRED_FEATURES:
            result['issues'].append(
                f"Expected {self.REQUIRED_FEATURES} features, got {len(feature_cols)}"
            )
            result['passed'] = False

        # Store feature names for later
        self.feature_names = feature_cols

        return result

    def _validate_features(self) -> Dict[str, Any]:
        """Verify all features present in all splits."""
        result = {
            'passed': True,
            'issues': [],
            'feature_count': len(self.feature_names) if self.feature_names else 0
        }

        if self.feature_names is None:
            return result

        for split_name, df in [('train', self.df_train), ('val', self.df_val), ('test', self.df_test)]:
            for feat in self.feature_names:
                if feat not in df.columns:
                    result['issues'].append(f"{split_name}: Missing feature {feat}")
                    result['passed'] = False

        return result

    def _validate_targets(self) -> Dict[str, Any]:
        """Verify target columns and values."""
        result = {
            'passed': True,
            'issues': [],
            'y_binary_unique': None,
            'y_continuous_range': None,
        }

        # Check y_binary
        if 'y_binary' not in self.df_train.columns:
            result['issues'].append("Missing y_binary column")
            result['passed'] = False
        else:
            unique_vals = self.df_train['y_binary'].unique()
            if not all(v in [True, False, 0, 1] for v in unique_vals):
                result['issues'].append(f"y_binary contains unexpected values: {unique_vals}")
                result['passed'] = False
            result['y_binary_unique'] = sorted(set(unique_vals))

        # Check y_continuous
        if 'y_continuous' not in self.df_train.columns:
            result['issues'].append("Missing y_continuous column")
            result['passed'] = False
        else:
            y_min = self.df_train['y_continuous'].min()
            y_max = self.df_train['y_continuous'].max()
            if not (0 <= y_min <= 1 and 0 <= y_max <= 1):
                result['issues'].append(
                    f"y_continuous outside [0, 1]: [{y_min}, {y_max}]"
                )
                # Not a hard fail; just a warning
            result['y_continuous_range'] = (y_min, y_max)

        return result

    def _validate_missing_values(self) -> Dict[str, Any]:
        """Verify no NaN in critical columns."""
        result = {
            'passed': True,
            'issues': [],
            'total_nan_train': 0,
            'total_nan_val': 0,
            'total_nan_test': 0,
        }

        # Feature columns should have NO NaN
        critical_cols = self.REQUIRED_METADATA + (self.feature_names or [])

        for split_name, df in [('train', self.df_train), ('val', self.df_val), ('test', self.df_test)]:
            nan_count = df[critical_cols].isnull().sum().sum()
            result[f'total_nan_{split_name}'] = nan_count

            if nan_count > 0:
                result['issues'].append(f"{split_name}: Found {nan_count} NaN values")
                result['passed'] = False

        return result

    def _validate_ranges(self) -> Dict[str, Any]:
        """Verify feature values in reasonable ranges."""
        result = {
            'passed': True,
            'issues': [],
            'out_of_range_features': []
        }

        if self.feature_names is None:
            return result

        for feat in self.feature_names:
            for split_name, df in [('train', self.df_train), ('val', self.df_val), ('test', self.df_test)]:
                col_data = df[feat]

                # Check for inf
                if np.isinf(col_data).any():
                    result['issues'].append(f"{split_name}/{feat}: Contains inf values")
                    result['passed'] = False

                # Check for extreme outliers (optional warning)
                q1 = col_data.quantile(0.25)
                q3 = col_data.quantile(0.75)
                iqr = q3 - q1
                if iqr > 0:
                    lower = q1 - 10 * iqr
                    upper = q3 + 10 * iqr
                    n_outliers = ((col_data < lower) | (col_data > upper)).sum()
                    if n_outliers > len(col_data) * 0.05:  # >5% outliers
                        result['out_of_range_features'].append(feat)

        return result

    def _validate_split_consistency(self) -> Dict[str, Any]:
        """Verify split assignments and no overlap."""
        result = {
            'passed': True,
            'issues': [],
            'split_distribution': {}
        }

        combined = pd.concat([self.df_train, self.df_val, self.df_test], ignore_index=True)

        # Check split column
        for split_name, df in [('train', self.df_train), ('val', self.df_val), ('test', self.df_test)]:
            split_vals = df['split'].unique()
            expected = split_name
            if len(split_vals) != 1 or split_vals[0] != expected:
                result['issues'].append(f"{split_name}: Unexpected split values {split_vals}")
                result['passed'] = False

        # Check for duplicates
        combined['key'] = combined['student_id'].astype(str) + '_' + combined['day'].astype(str)
        if combined['key'].duplicated().any():
            result['issues'].append("Found duplicate (student_id, day) pairs across splits")
            result['passed'] = False

        result['split_distribution'] = {
            'train': len(self.df_train),
            'val': len(self.df_val),
            'test': len(self.df_test),
            'total': len(combined)
        }

        return result

    def get_features(self) -> List[str]:
        """Get list of feature names."""
        if self.feature_names is None:
            raise ValueError("Call validate() first to populate feature_names")
        return self.feature_names.copy()

    def get_X_y(self, split: str = 'train') -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Get features and targets for a split.

        Args:
            split: 'train', 'val', or 'test'

        Returns:
            (X, y_binary, y_continuous)
        """
        if split == 'train':
            df = self.df_train
        elif split == 'val':
            df = self.df_val
        elif split == 'test':
            df = self.df_test
        else:
            raise ValueError(f"Unknown split: {split}")

        if df is None:
            raise ValueError("Dataset not loaded. Call load() first.")

        X = df[self.feature_names].values.astype(np.float32)
        y_binary = df['y_binary'].astype(bool).values
        y_continuous = df['y_continuous'].astype(np.float32).values

        return X, y_binary, y_continuous

    def get_metadata(self, split: str = 'train') -> pd.DataFrame:
        """Get metadata columns for a split."""
        if split == 'train':
            df = self.df_train
        elif split == 'val':
            df = self.df_val
        elif split == 'test':
            df = self.df_test
        else:
            raise ValueError(f"Unknown split: {split}")

        return df[self.REQUIRED_METADATA].copy()

    def _get_feature_columns(self) -> List[str]:
        """Extract feature columns in the authoritative production order."""
        cols = [c for c in self.df_train.columns if c.startswith(self.FEATURE_PREFIX)]
        validate_prefixed_feature_columns(cols)
        return prefixed_feature_order()

    def _print_validation_results(self, results: Dict[str, Any]) -> None:
        """Pretty-print validation results."""
        print("\n" + "=" * 70)
        print("DATASET VALIDATION RESULTS")
        print("=" * 70)

        for check_name, check_result in results.items():
            if check_name == 'all_passed':
                continue

            if isinstance(check_result, dict):
                passed = check_result.get('passed', False)
                status = "[PASS]" if passed else "[FAIL]"
                print(f"\n{status}: {check_name}")

                if check_result.get('issues'):
                    for issue in check_result['issues']:
                        print(f"  ! {issue}")

                # Print other details
                for k, v in check_result.items():
                    if k not in ['passed', 'issues']:
                        if isinstance(v, (dict, list)):
                            print(f"  {k}: {v}")
                        elif not isinstance(v, bool):
                            print(f"  {k}: {v}")

        print("\n" + "=" * 70)
        overall = "[PASSED]" if results['all_passed'] else "[FAILED]"
        print(f"Overall: {overall}")
        print("=" * 70 + "\n")


def main():
    """Test data loader."""
    loader = DataLoader(
        'data/phase3/train.csv',
        'data/phase3/val.csv',
        'data/phase3/test.csv'
    )

    df_train, df_val, df_test = loader.load()
    results = loader.validate()

    if results['all_passed']:
        print("Dataset is valid and ready for ML pipeline.")
        X_train, y_train_binary, y_train_continuous = loader.get_X_y('train')
        print(f"\nTrain set shape: X={X_train.shape}, y_binary={y_train_binary.shape}")
    else:
        print("Dataset validation failed. Fix issues before proceeding.")
        return 1

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
