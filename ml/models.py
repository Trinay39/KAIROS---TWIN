"""
KAIROS-TWIN Phase 4: Models.

Three baseline models for binary overload prediction:
1. Logistic Regression
2. Random Forest
3. XGBoost
"""
from __future__ import annotations
from typing import Dict, Any
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False


class BaselineLogistic:
    """Logistic Regression baseline."""

    def __init__(self, C: float = 1.0, random_state: int = 42):
        """
        Initialize Logistic Regression.

        Args:
            C: Regularization strength (1/lambda)
            random_state: Random seed
        """
        self.C = C
        self.random_state = random_state
        self.model = LogisticRegression(
            C=C,
            penalty='l2',
            solver='lbfgs',
            max_iter=1000,
            random_state=random_state,
            n_jobs=-1
        )
        self.is_fitted = False

    def fit(self, X_train: np.ndarray, y_train: np.ndarray) -> BaselineLogistic:
        """Fit model."""
        self.model.fit(X_train, y_train)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Get binary predictions."""
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Get probability estimates."""
        return self.model.predict_proba(X)

    def get_params(self) -> Dict[str, Any]:
        """Get model parameters."""
        return {'C': self.C, 'random_state': self.random_state}

    def __repr__(self) -> str:
        return f"BaselineLogistic(C={self.C})"


class BaselineRandomForest:
    """Random Forest baseline."""

    def __init__(
        self,
        n_estimators: int = 200,
        max_depth: int = None,
        min_samples_leaf: int = 1,
        max_features: str = 'sqrt',
        random_state: int = 42
    ):
        """
        Initialize Random Forest.

        Args:
            n_estimators: Number of trees
            max_depth: Max tree depth
            min_samples_leaf: Min samples per leaf
            max_features: Feature selection strategy
            random_state: Random seed
        """
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.max_features = max_features
        self.random_state = random_state

        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_leaf=min_samples_leaf,
            max_features=max_features,
            random_state=random_state,
            n_jobs=-1
        )
        self.is_fitted = False

    def fit(self, X_train: np.ndarray, y_train: np.ndarray) -> BaselineRandomForest:
        """Fit model."""
        self.model.fit(X_train, y_train)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Get binary predictions."""
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Get probability estimates."""
        return self.model.predict_proba(X)

    def get_params(self) -> Dict[str, Any]:
        """Get model parameters."""
        return {
            'n_estimators': self.n_estimators,
            'max_depth': self.max_depth,
            'min_samples_leaf': self.min_samples_leaf,
            'max_features': self.max_features,
            'random_state': self.random_state,
        }

    def __repr__(self) -> str:
        return (
            f"BaselineRandomForest("
            f"n_est={self.n_estimators}, "
            f"max_depth={self.max_depth})"
        )


class BaselineXGBoost:
    """XGBoost baseline (if available)."""

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 3,
        learning_rate: float = 0.1,
        subsample: float = 1.0,
        colsample_bytree: float = 1.0,
        random_state: int = 42
    ):
        """
        Initialize XGBoost.

        Args:
            n_estimators: Number of boosting rounds
            max_depth: Max tree depth
            learning_rate: Learning rate (eta)
            subsample: Subsample ratio
            colsample_bytree: Feature subsample ratio
            random_state: Random seed
        """
        if not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost not installed. Install with: pip install xgboost")

        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.random_state = random_state

        self.model = xgb.XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=subsample,
            colsample_bytree=colsample_bytree,
            random_state=random_state,
            objective='binary:logistic',
            n_jobs=-1,
            verbosity=0
        )
        self.is_fitted = False

    def fit(self, X_train: np.ndarray, y_train: np.ndarray) -> BaselineXGBoost:
        """Fit model."""
        self.model.fit(X_train, y_train)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Get binary predictions."""
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Get probability estimates."""
        return self.model.predict_proba(X)

    def get_params(self) -> Dict[str, Any]:
        """Get model parameters."""
        return {
            'n_estimators': self.n_estimators,
            'max_depth': self.max_depth,
            'learning_rate': self.learning_rate,
            'subsample': self.subsample,
            'colsample_bytree': self.colsample_bytree,
            'random_state': self.random_state,
        }

    def __repr__(self) -> str:
        return (
            f"BaselineXGBoost("
            f"n_est={self.n_estimators}, "
            f"lr={self.learning_rate})"
        )


def main():
    """Test model initialization."""
    print("Testing model classes...")

    lr = BaselineLogistic(C=1.0)
    print(f"  LogReg: {lr}")

    rf = BaselineRandomForest(n_estimators=200, max_depth=10)
    print(f"  RF: {rf}")

    if XGBOOST_AVAILABLE:
        xgb_model = BaselineXGBoost(n_estimators=100, max_depth=5)
        print(f"  XGBoost: {xgb_model}")
    else:
        print("  XGBoost: NOT AVAILABLE (optional)")

    print("\nModel classes initialized successfully!")
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
