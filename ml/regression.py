"""
KAIROS-TWIN Phase 4: Regression.

Predict continuous strain_index (secondary task).
"""
from __future__ import annotations
from typing import Dict, Tuple, Any
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


class RegressionEvaluator:
    """Evaluate regression on strain_index."""

    @staticmethod
    def compute_metrics(
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> Dict[str, float]:
        """Compute regression metrics."""
        y_true = np.asarray(y_true, dtype=np.float32)
        y_pred = np.asarray(y_pred, dtype=np.float32)

        mae = mean_absolute_error(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_true, y_pred)

        # Pearson correlation
        correlation = np.corrcoef(y_true, y_pred)[0, 1]

        return {
            'mae': float(mae),
            'mse': float(mse),
            'rmse': float(rmse),
            'r2': float(r2),
            'pearson_r': float(correlation),
            'mean_y_true': float(y_true.mean()),
            'std_y_true': float(y_true.std()),
            'mean_y_pred': float(y_pred.mean()),
            'std_y_pred': float(y_pred.std()),
        }
