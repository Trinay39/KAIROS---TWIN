"""
KAIROS-TWIN Phase 4: Training.

Hyperparameter tuning on TRAIN split using TimeSeriesSplit.
"""
from __future__ import annotations
from typing import Dict, Tuple, Any, List
import numpy as np
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from ml.models import BaselineLogistic, BaselineRandomForest, BaselineXGBoost


class ModelTrainer:
    """Train models with hyperparameter tuning on TRAIN only."""

    def __init__(self, random_state: int = 42):
        """Initialize trainer."""
        self.random_state = random_state
        self.best_params = None
        self.cv_results = None

    def tune_logistic(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Tune Logistic Regression using TimeSeriesSplit."""
        param_grid = {
            'C': [0.001, 0.01, 0.1, 1, 10, 100],
        }

        tscv = TimeSeriesSplit(n_splits=5)

        grid_search = GridSearchCV(
            BaselineLogistic(random_state=self.random_state).model,
            param_grid,
            cv=tscv,
            scoring='roc_auc',
            n_jobs=-1,
            verbose=0
        )

        grid_search.fit(X_train, y_train)

        best_params = {'C': grid_search.best_params_['C']}
        cv_results = {
            'best_score': grid_search.best_score_,
            'best_params': best_params,
            'cv_scores': grid_search.cv_results_['mean_test_score'].tolist(),
        }

        return best_params, cv_results

    def tune_random_forest(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Tune Random Forest using TimeSeriesSplit."""
        param_grid = {
            'n_estimators': [200, 500],
            'max_depth': [None, 5, 10, 20],
            'min_samples_leaf': [1, 2, 5],
            'max_features': ['sqrt', 'log2'],
        }

        tscv = TimeSeriesSplit(n_splits=5)

        grid_search = GridSearchCV(
            BaselineRandomForest(random_state=self.random_state).model,
            param_grid,
            cv=tscv,
            scoring='roc_auc',
            n_jobs=-1,
            verbose=0
        )

        grid_search.fit(X_train, y_train)

        best_params = {
            'n_estimators': grid_search.best_params_['n_estimators'],
            'max_depth': grid_search.best_params_['max_depth'],
            'min_samples_leaf': grid_search.best_params_['min_samples_leaf'],
            'max_features': grid_search.best_params_['max_features'],
        }

        cv_results = {
            'best_score': grid_search.best_score_,
            'best_params': best_params,
            'cv_scores': grid_search.cv_results_['mean_test_score'].tolist(),
        }

        return best_params, cv_results

    def tune_xgboost(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Tune XGBoost using TimeSeriesSplit."""
        try:
            import xgboost as xgb
        except ImportError:
            return {}, {'available': False, 'reason': 'XGBoost not installed'}

        param_grid = {
            'n_estimators': [100, 300, 500],
            'max_depth': [3, 5, 7],
            'learning_rate': [0.01, 0.05, 0.1],
            'subsample': [0.8, 1.0],
            'colsample_bytree': [0.8, 1.0],
        }

        tscv = TimeSeriesSplit(n_splits=5)

        grid_search = GridSearchCV(
            BaselineXGBoost(random_state=self.random_state).model,
            param_grid,
            cv=tscv,
            scoring='roc_auc',
            n_jobs=-1,
            verbose=0
        )

        grid_search.fit(X_train, y_train)

        best_params = {
            'n_estimators': grid_search.best_params_['n_estimators'],
            'max_depth': grid_search.best_params_['max_depth'],
            'learning_rate': grid_search.best_params_['learning_rate'],
            'subsample': grid_search.best_params_['subsample'],
            'colsample_bytree': grid_search.best_params_['colsample_bytree'],
        }

        cv_results = {
            'best_score': grid_search.best_score_,
            'best_params': best_params,
            'cv_scores': grid_search.cv_results_['mean_test_score'].tolist(),
        }

        return best_params, cv_results
