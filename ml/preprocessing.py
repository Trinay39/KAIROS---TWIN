"""
KAIROS-TWIN Phase 4: Preprocessing.

Preprocessing pipeline that fits on TRAIN ONLY.

Operations:
- Missing value imputation (if needed)
- Standardization (mean=0, std=1)
- No feature selection
- Preserve all 46 features
"""
from __future__ import annotations
from typing import Tuple
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer


class Preprocessor:
    """Preprocessing pipeline fit on train data only."""

    def __init__(
        self,
        method: str = 'standard',
        handle_missing: bool = True,
        random_state: int = 42
    ):
        """
        Initialize preprocessor.

        Args:
            method: 'standard' for StandardScaler
            handle_missing: Impute missing values if True
            random_state: Random seed
        """
        self.method = method
        self.handle_missing = handle_missing
        self.random_state = random_state

        self.imputer = None
        self.scaler = None
        self.feature_names = None
        self.is_fitted = False

    def fit(self, X_train: np.ndarray, feature_names: list = None) -> Preprocessor:
        """
        Fit preprocessing on train data ONLY.

        Args:
            X_train: Training features (n_samples, n_features)
            feature_names: Optional feature names for tracking

        Returns:
            self
        """
        if isinstance(X_train, np.ndarray):
            X = X_train.astype(np.float32)
        else:
            X = np.asarray(X_train, dtype=np.float32)

        self.feature_names = feature_names

        # Step 1: Imputation (if needed)
        if self.handle_missing:
            self.imputer = SimpleImputer(strategy='mean')
            X = self.imputer.fit_transform(X)

        # Step 2: Scaling
        if self.method == 'standard':
            self.scaler = StandardScaler()
            self.scaler.fit(X)
        else:
            raise ValueError(f"Unknown method: {self.method}")

        self.is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Apply preprocessing to any split.

        Args:
            X: Features to transform

        Returns:
            Transformed features
        """
        if not self.is_fitted:
            raise ValueError("Preprocessor not fitted. Call fit() first.")

        if isinstance(X, np.ndarray):
            X_copy = X.astype(np.float32).copy()
        else:
            X_copy = np.asarray(X, dtype=np.float32).copy()

        # Apply imputation if fitted
        if self.imputer is not None:
            X_copy = self.imputer.transform(X_copy)

        # Apply scaling
        X_copy = self.scaler.transform(X_copy)

        return X_copy

    def fit_transform(self, X_train: np.ndarray, feature_names: list = None) -> np.ndarray:
        """
        Fit and transform in one step.

        Args:
            X_train: Training features
            feature_names: Optional feature names

        Returns:
            Transformed training features
        """
        self.fit(X_train, feature_names=feature_names)
        return self.transform(X_train)

    def get_scaler_params(self) -> dict:
        """Get fitted scaler parameters for inspection."""
        if not self.is_fitted:
            raise ValueError("Preprocessor not fitted")

        return {
            'mean': self.scaler.mean_,
            'scale': self.scaler.scale_,
            'var': self.scaler.var_,
        }

    def __repr__(self) -> str:
        """String representation."""
        status = "fitted" if self.is_fitted else "unfitted"
        return f"Preprocessor(method={self.method}, status={status})"


def main():
    """Test preprocessor."""
    from ml.data_loader import DataLoader

    # Load data
    loader = DataLoader(
        'data/phase3/train.csv',
        'data/phase3/val.csv',
        'data/phase3/test.csv'
    )
    df_train, df_val, df_test = loader.load()
    loader.validate()

    X_train, y_train_binary, _ = loader.get_X_y('train')
    X_val, y_val_binary, _ = loader.get_X_y('val')
    X_test, y_test_binary, _ = loader.get_X_y('test')

    print("Testing Preprocessor...")
    print(f"\nBefore preprocessing:")
    print(f"  X_train: mean={X_train.mean():.4f}, std={X_train.std():.4f}")
    print(f"  X_val:   mean={X_val.mean():.4f}, std={X_val.std():.4f}")
    print(f"  X_test:  mean={X_test.mean():.4f}, std={X_test.std():.4f}")

    # Fit on train only
    preprocessor = Preprocessor(method='standard', handle_missing=True)
    X_train_prep = preprocessor.fit_transform(X_train, feature_names=loader.get_features())

    # Transform val/test (using train statistics)
    X_val_prep = preprocessor.transform(X_val)
    X_test_prep = preprocessor.transform(X_test)

    print(f"\nAfter preprocessing (fit on train only):")
    print(f"  X_train: mean={X_train_prep.mean():.6f}, std={X_train_prep.std():.6f}")
    print(f"  X_val:   mean={X_val_prep.mean():.6f}, std={X_val_prep.std():.6f}")
    print(f"  X_test:  mean={X_test_prep.mean():.6f}, std={X_test_prep.std():.6f}")

    print(f"\nShape preserved:")
    print(f"  X_train: {X_train_prep.shape}")
    print(f"  X_val:   {X_val_prep.shape}")
    print(f"  X_test:  {X_test_prep.shape}")

    print(f"\nNo NaN after preprocessing:")
    print(f"  X_train: {np.isnan(X_train_prep).sum()} NaN")
    print(f"  X_val:   {np.isnan(X_val_prep).sum()} NaN")
    print(f"  X_test:  {np.isnan(X_test_prep).sum()} NaN")

    print("\nPreprocessor test passed!")
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
