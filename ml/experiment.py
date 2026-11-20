"""
KAIROS-TWIN Phase 4: Experiment.

Orchestrates entire ML pipeline with reproducibility.
"""
from __future__ import annotations
from typing import Dict, List, Any, Tuple
from pathlib import Path
import json
import pickle
import numpy as np
from datetime import datetime
from sklearn.pipeline import Pipeline

from ml.data_loader import DataLoader
from ml.preprocessing import Preprocessor
from ml.models import BaselineLogistic, BaselineRandomForest, BaselineXGBoost
from ml.train import ModelTrainer
from ml.evaluate import Evaluator
from ml.calibration import CalibrationAnalyzer
from ml.interpretability import FeatureImportance
from ml.regression import RegressionEvaluator
from ml.feature_contract import raw_feature_order


class Experiment:
    """Complete ML experiment orchestrator."""

    def __init__(
        self,
        output_dir: str = 'experiments/results',
        random_state: int = 42,
        verbose: bool = True
    ):
        """
        Initialize experiment.

        Args:
            output_dir: Output directory for results
            random_state: Random seed
            verbose: Print progress
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.random_state = random_state
        self.verbose = verbose

        self.results = {}
        self.models = {}
        self.metadata = {
            'random_state': random_state,
            'timestamp': datetime.now().isoformat(),
            'cv_strategy': 'TimeSeriesSplit(n_splits=5)',
        }

    def run(self) -> Dict[str, Any]:
        """Execute complete pipeline."""
        if self.verbose:
            print("\n" + "=" * 70)
            print("KAIROS-TWIN PHASE 4: ML PIPELINE")
            print("=" * 70)

        # Step 1: Load and validate data
        if self.verbose:
            print("\n[Step 1/6] Loading data...")
        loader = DataLoader(
            'data/phase3/train.csv',
            'data/phase3/val.csv',
            'data/phase3/test.csv',
            verbose=False
        )
        df_train, df_val, df_test = loader.load()
        loader.validate()
        feature_names = loader.get_features()
        self.metadata['feature_names'] = feature_names

        X_train, y_train_binary, y_train_continuous = loader.get_X_y('train')
        X_val, y_val_binary, y_val_continuous = loader.get_X_y('val')
        X_test, y_test_binary, y_test_continuous = loader.get_X_y('test')

        if self.verbose:
            print(f"  Train: {X_train.shape}, Val: {X_val.shape}, Test: {X_test.shape}")

        # Step 2: Preprocessing (fit on train only)
        if self.verbose:
            print("\n[Step 2/6] Preprocessing (fit on train only)...")
        preprocessor = Preprocessor(method='standard', handle_missing=True)
        X_train_prep = preprocessor.fit_transform(X_train, feature_names=feature_names)
        X_val_prep = preprocessor.transform(X_val)
        X_test_prep = preprocessor.transform(X_test)

        if self.verbose:
            print(f"  Train mean={X_train_prep.mean():.4f}, std={X_train_prep.std():.4f}")

        # Step 3: Train models with hyperparameter tuning
        if self.verbose:
            print("\n[Step 3/6] Training models (hyperparameter tuning on train only)...")

        trainer = ModelTrainer(random_state=self.random_state)

        # Logistic Regression
        lr_params, lr_cv = trainer.tune_logistic(X_train_prep, y_train_binary)
        model_lr = BaselineLogistic(**lr_params, random_state=self.random_state)
        model_lr.fit(X_train_prep, y_train_binary)
        self.models['logistic'] = model_lr

        # Random Forest
        rf_params, rf_cv = trainer.tune_random_forest(X_train_prep, y_train_binary)
        model_rf = BaselineRandomForest(**rf_params, random_state=self.random_state)
        model_rf.fit(X_train_prep, y_train_binary)
        self.models['rf'] = model_rf

        # XGBoost (optional)
        model_xgb = None
        xgb_params = {}
        xgb_cv = {}
        try:
            xgb_params, xgb_cv = trainer.tune_xgboost(X_train_prep, y_train_binary)
            if xgb_params:
                model_xgb = BaselineXGBoost(**xgb_params, random_state=self.random_state)
                model_xgb.fit(X_train_prep, y_train_binary)
                self.models['xgboost'] = model_xgb
                if self.verbose:
                    print("  - XGBoost: tuned and trained")
            else:
                if self.verbose:
                    print("  - XGBoost: not available")
        except Exception as e:
            if self.verbose:
                print(f"  - XGBoost: error ({e})")

        if self.verbose:
            print(f"  - Logistic Regression: C={lr_params['C']}, CV AUC={lr_cv['best_score']:.4f}")
            print(f"  - Random Forest: CV AUC={rf_cv['best_score']:.4f}")

        # Step 4: Evaluate on validation set
        if self.verbose:
            print("\n[Step 4/6] Evaluating on validation set...")

        results_lr_val = self._evaluate_model(
            'logistic', model_lr, X_val_prep, y_val_binary, 'val'
        )
        results_rf_val = self._evaluate_model(
            'rf', model_rf, X_val_prep, y_val_binary, 'val'
        )

        # Find optimal threshold on validation set
        y_val_proba_lr = model_lr.predict_proba(X_val_prep)[:, 1]
        optimal_threshold_lr, _ = Evaluator.find_optimal_threshold(y_val_binary, y_val_proba_lr, metric='f1')
        production_model_name = 'rf'
        production_threshold = 0.5

        if self.verbose:
            print(f"  - Logistic: ROC-AUC={results_lr_val['roc_auc']:.4f}")
            print(f"  - RF: ROC-AUC={results_rf_val['roc_auc']:.4f}")
            print(f"  - Optimal threshold (LogReg): {optimal_threshold_lr:.3f}")
            print(f"  - Production model: RF threshold={production_threshold:.3f}")

        # Step 5: Evaluate on test set (final, locked threshold)
        if self.verbose:
            print("\n[Step 5/6] Evaluating on test set (FINAL)...")

        results_lr_test = self._evaluate_model(
            'logistic', model_lr, X_test_prep, y_test_binary, 'test',
            threshold=optimal_threshold_lr
        )
        results_rf_test = self._evaluate_model(
            'rf', model_rf, X_test_prep, y_test_binary, 'test',
            threshold=0.5  # Use default for RF
        )

        if self.verbose:
            print(f"  - Logistic (threshold={optimal_threshold_lr:.3f}): ROC-AUC={results_lr_test['roc_auc']:.4f}, F1={results_lr_test['f1']:.4f}")
            print(f"  - RF (threshold=0.5): ROC-AUC={results_rf_test['roc_auc']:.4f}, F1={results_rf_test['f1']:.4f}")

        # Step 6: Save results
        if self.verbose:
            print("\n[Step 6/6] Saving results...")

        self._save_results(
            models={'logistic': model_lr, 'rf': model_rf, 'xgboost': model_xgb},
            results={
                'logistic': {'val': results_lr_val, 'test': results_lr_test},
                'rf': {'val': results_rf_val, 'test': results_rf_test},
            },
            production_model=model_rf,
            production_model_name=production_model_name,
            production_threshold=production_threshold,
            preprocessor=preprocessor,
            feature_names=feature_names,
            preprocessing_params=preprocessor.get_scaler_params(),
            hyperparams={'logistic': lr_params, 'rf': rf_params, 'xgboost': xgb_params},
            cv_results={'logistic': lr_cv, 'rf': rf_cv, 'xgboost': xgb_cv},
            optimal_threshold=optimal_threshold_lr
        )

        if self.verbose:
            print("[OK] Experiment complete!")
            print("=" * 70 + "\n")

        return {
            'models': self.models,
            'results': self.results,
            'metadata': self.metadata,
        }

    def _evaluate_model(
        self,
        model_name: str,
        model,
        X: np.ndarray,
        y: np.ndarray,
        split: str,
        threshold: float = 0.5
    ) -> Dict[str, any]:
        """Evaluate a single model."""
        y_pred = model.predict(X)
        y_proba = model.predict_proba(X)[:, 1]

        metrics = Evaluator.compute_metrics(y, y_pred, y_proba, threshold=threshold)

        # Feature importance
        feat_names = self.metadata.get('feature_names', [])
        importance = {}

        if model_name == 'logistic':
            importance = FeatureImportance.logistic_coefficients(model.model, feat_names or [])
        elif model_name == 'rf':
            importance = FeatureImportance.rf_importance(model.model, feat_names or [])

        # Calibration (on val/test)
        calib = CalibrationAnalyzer.compute_calibration_metrics(y, y_proba, n_bins=10)

        return {
            **metrics,
            'importance': importance,
            'calibration': calib,
        }

    def _save_results(
        self,
        models: Dict,
        results: Dict,
        production_model,
        production_model_name: str,
        production_threshold: float,
        preprocessor: Preprocessor,
        feature_names: List[str],
        preprocessing_params: Dict,
        hyperparams: Dict,
        cv_results: Dict,
        optimal_threshold: float
    ) -> None:
        """Save all results to disk."""
        # Save models
        for name, model in models.items():
            if model is not None:
                path = self.output_dir / f"{name}.pkl"
                with open(path, 'wb') as f:
                    pickle.dump(model, f)

        production_pipeline = Pipeline([
            ('imputer', preprocessor.imputer),
            ('scaler', preprocessor.scaler),
            ('classifier', production_model.model),
        ])
        production_artifact = {
            'artifact_type': 'kairos_twin_production_pipeline',
            'artifact_version': '1.0',
            'model_name': production_model_name,
            'model_version': '1.0',
            'pipeline': production_pipeline,
            'feature_names': list(feature_names),
            'raw_feature_names': raw_feature_order(),
            'feature_count': len(feature_names),
            'threshold': float(production_threshold),
            'threshold_source': 'fixed_default_for_served_rf_model',
            'calibrated': False,
            'calibration_method': None,
            'calibration_note': 'Calibration was analyzed only; no calibrator is trained or applied in production.',
            'random_state': self.random_state,
            'training_data': {
                'train_path': 'data/phase3/train.csv',
                'val_path': 'data/phase3/val.csv',
                'test_path': 'data/phase3/test.csv',
            },
            'preprocessing': {
                'imputer': 'SimpleImputer(strategy=mean)',
                'scaler': 'StandardScaler',
                'fit_scope': 'train_split_only',
            },
        }
        with open(self.output_dir / 'model_pipeline.pkl', 'wb') as f:
            pickle.dump(production_artifact, f)

        # Save metrics
        for model_name, model_results in results.items():
            model_dir = self.output_dir / model_name
            model_dir.mkdir(exist_ok=True)

            with open(model_dir / 'metrics.json', 'w') as f:
                json.dump(model_results, f, indent=2)

        # Save metadata
        metadata = {
            'random_state': self.random_state,
            'timestamp': self.metadata['timestamp'],
            'cv_strategy': self.metadata['cv_strategy'],
            'production_artifact': 'model_pipeline.pkl',
            'production_model_name': production_model_name,
            'production_model_version': '1.0',
            'production_threshold': float(production_threshold),
            'production_threshold_source': 'fixed_default_for_served_rf_model',
            'calibrated': False,
            'calibration_method': None,
            'calibration_note': 'Calibration was analyzed only; no calibrator is trained or applied in production.',
            'feature_count': len(feature_names),
            'feature_names': feature_names,
            'raw_feature_names': raw_feature_order(),
            'optimal_threshold': optimal_threshold,
            'optimal_threshold_model': 'logistic',
            'hyperparams': hyperparams,
            'cv_results': cv_results,
            'preprocessing': {
                'imputer': 'SimpleImputer(strategy=mean)',
                'scaler': 'StandardScaler',
                'fit_scope': 'train_split_only',
                'scaler_mean': preprocessing_params['mean'].tolist(),
                'scaler_scale': preprocessing_params['scale'].tolist(),
                'scaler_var': preprocessing_params['var'].tolist(),
            },
            'training_data': {
                'train_path': 'data/phase3/train.csv',
                'val_path': 'data/phase3/val.csv',
                'test_path': 'data/phase3/test.csv',
            },
        }

        with open(self.output_dir / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)

        if self.verbose:
            print(f"  Saved to {self.output_dir}/")
