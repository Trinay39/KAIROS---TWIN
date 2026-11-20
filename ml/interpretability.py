"""
KAIROS-TWIN Phase 4: Interpretability.

Feature importance and model interpretation.
"""
from __future__ import annotations
from typing import Dict, List, Tuple, Any
import numpy as np
from sklearn.inspection import permutation_importance


class FeatureImportance:
    """Extract and analyze feature importance."""

    @staticmethod
    def rf_importance(model, feature_names: List[str]) -> Dict[str, float]:
        """Extract Random Forest feature importance."""
        importances = model.feature_importances_
        return dict(zip(feature_names, importances))

    @staticmethod
    def logistic_coefficients(model, feature_names: List[str]) -> Dict[str, float]:
        """Extract Logistic Regression coefficients (standardized)."""
        coefs = model.coef_[0]  # Shape (n_features,)
        abs_coefs = np.abs(coefs)
        normalized = abs_coefs / abs_coefs.sum()
        return dict(zip(feature_names, normalized))

    @staticmethod
    def permutation_importance(
        model,
        X_test: np.ndarray,
        y_test: np.ndarray,
        feature_names: List[str],
        n_repeats: int = 10,
        random_state: int = 42
    ) -> Dict[str, float]:
        """Compute permutation importance."""
        perm_imp = permutation_importance(
            model, X_test, y_test,
            n_repeats=n_repeats,
            random_state=random_state,
            n_jobs=-1
        )
        return dict(zip(feature_names, perm_imp.importances_mean))

    @staticmethod
    def get_top_features(
        importance_dict: Dict[str, float],
        top_n: int = 15
    ) -> List[Tuple[str, float]]:
        """Get top N features by importance."""
        sorted_feat = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
        return sorted_feat[:top_n]

    @staticmethod
    def try_shap_importance(model, X_test: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
        """Attempt SHAP importance (optional)."""
        try:
            import shap

            # Create explainer (TreeExplainer for tree models)
            if hasattr(model, 'estimators_'):  # Random Forest
                explainer = shap.TreeExplainer(model)
            else:
                return {'available': False, 'reason': 'SHAP not supported for this model'}

            shap_values = explainer.shap_values(X_test)

            # Handle binary classification (may return list of 2 arrays)
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # Use positive class

            mean_abs_shap = np.abs(shap_values).mean(axis=0)
            return {
                'available': True,
                'importance': dict(zip(feature_names, mean_abs_shap))
            }
        except ImportError:
            return {'available': False, 'reason': 'SHAP not installed'}
        except Exception as e:
            return {'available': False, 'reason': str(e)}
