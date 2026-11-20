"""
KAIROS-TWIN Phase 4: Calibration.

Probability calibration analysis and methods.
"""
from __future__ import annotations
from typing import Dict, Tuple, Any
import numpy as np
from sklearn.calibration import calibration_curve, CalibratedClassifierCV
from sklearn.metrics import brier_score_loss


class CalibrationAnalyzer:
    """Calibration analysis and correction."""

    @staticmethod
    def compute_calibration_metrics(
        y_true: np.ndarray,
        y_proba: np.ndarray,
        n_bins: int = 10
    ) -> Dict[str, Any]:
        """Compute calibration metrics."""
        y_true = np.asarray(y_true, dtype=bool)
        y_proba = np.asarray(y_proba, dtype=np.float32).ravel()

        # Calibration curve
        prob_true, prob_pred = calibration_curve(y_true, y_proba, n_bins=n_bins)

        # Expected Calibration Error
        ece = np.mean(np.abs(prob_pred - prob_true))

        # Maximum Calibration Error
        mce = np.max(np.abs(prob_pred - prob_true))

        # Brier score
        brier = brier_score_loss(y_true, y_proba)

        return {
            'prob_true': prob_true.tolist(),
            'prob_pred': prob_pred.tolist(),
            'ece': float(ece),
            'mce': float(mce),
            'brier': float(brier),
        }

    @staticmethod
    def apply_platt_scaling(
        y_train: np.ndarray,
        y_proba_train: np.ndarray,
        y_proba_test: np.ndarray
    ) -> np.ndarray:
        """Apply Platt scaling to test probabilities."""
        from sklearn.linear_model import LogisticRegression

        y_train = np.asarray(y_train, dtype=bool)
        y_proba_train = np.asarray(y_proba_train, dtype=np.float32).ravel()
        y_proba_test = np.asarray(y_proba_test, dtype=np.float32).ravel()

        platt = LogisticRegression(max_iter=1000, random_state=42)
        platt.fit(y_proba_train.reshape(-1, 1), y_train)

        y_proba_calibrated = platt.predict_proba(y_proba_test.reshape(-1, 1))[:, 1]
        return y_proba_calibrated

    @staticmethod
    def apply_isotonic_regression(
        y_train: np.ndarray,
        y_proba_train: np.ndarray,
        y_proba_test: np.ndarray
    ) -> np.ndarray:
        """Apply isotonic regression to test probabilities."""
        from sklearn.isotonic import IsotonicRegression

        y_train = np.asarray(y_train, dtype=bool)
        y_proba_train = np.asarray(y_proba_train, dtype=np.float32).ravel()
        y_proba_test = np.asarray(y_proba_test, dtype=np.float32).ravel()

        iso = IsotonicRegression(out_of_bounds='clip')
        iso.fit(y_proba_train, y_train)

        y_proba_calibrated = iso.predict(y_proba_test)
        return y_proba_calibrated
