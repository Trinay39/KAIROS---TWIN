"""
KAIROS-TWIN Phase 5: Prediction Service.

Loads trained Phase 4 model artifacts and provides prediction interface.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from pathlib import Path
import pickle
import json
from dataclasses import dataclass
from datetime import datetime
import numpy as np

from core.schemas import StudentTwinState
from ml.feature_contract import EXPECTED_FEATURE_COUNT, raw_feature_order


@dataclass
class PredictionSnapshot:
    """Prediction output snapshot."""

    overload_probability: float  # [0, 1]
    overload_prediction: bool    # binary
    strain_index: Optional[float] = None  # [0, 1], regression target
    model_name: str = "random_forest"
    model_version: str = "1.0"
    timestamp: str = ""
    day: int = 0
    top_contributing_features: Dict[str, float] = None  # global RF importances, not local drivers
    confidence_info: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'overload_probability': float(self.overload_probability),
            'overload_prediction': bool(self.overload_prediction),
            'strain_index': float(self.strain_index) if self.strain_index is not None else None,
            'model_name': self.model_name,
            'model_version': self.model_version,
            'timestamp': self.timestamp,
            'day': int(self.day),
            'top_contributing_features': self.top_contributing_features or {},
            'confidence_info': self.confidence_info or {},
        }


class PredictionService:
    """
    Loads and manages trained Phase 4 model artifacts.

    Provides prediction interface: predict(twin_state) -> PredictionSnapshot

    Models are fixed (not retrained).
    """

    def __init__(
        self,
        model_dir: str = 'experiments/results',
        model_name: str = 'rf'
    ):
        """
        Initialize prediction service.

        Args:
            model_dir: Directory containing trained models
            model_name: Model to load ('rf', 'logistic', 'xgboost')
        """
        self.model_dir = Path(model_dir)
        self.model_name = model_name
        self.model = None
        self.pipeline = None
        self.metadata: Dict[str, Any] = {}
        self.regressor = None
        self.feature_names = raw_feature_order()
        self.threshold = 0.5
        self.calibrated = False
        self.is_loaded = False

        self._load_models()

    def _load_models(self) -> None:
        """Load trained models from disk."""
        pipeline_path = self.model_dir / "model_pipeline.pkl"

        if pipeline_path.exists():
            with open(pipeline_path, 'rb') as f:
                artifact = pickle.load(f)

            if not isinstance(artifact, dict) or 'pipeline' not in artifact:
                raise ValueError(f"Invalid production artifact: {pipeline_path}")

            artifact_features = artifact.get('raw_feature_names') or artifact.get('feature_names')
            if list(artifact_features or []) != raw_feature_order():
                raise ValueError(
                    "Production artifact feature order does not match FeatureEngine.FEATURE_NAMES"
                )

            self.pipeline = artifact['pipeline']
            self.model = self.pipeline.named_steps.get('classifier')
            self.model_name = artifact.get('model_name', self.model_name)
            self.feature_names = list(artifact_features)
            self.threshold = float(artifact.get('threshold', 0.5))
            self.calibrated = bool(artifact.get('calibrated', False))
            self.metadata = artifact
            loaded_path = pipeline_path
        else:
            model_path = self.model_dir / f"{self.model_name}.pkl"
            if not model_path.exists():
                raise FileNotFoundError(f"Model not found: {model_path}")

            with open(model_path, 'rb') as f:
                legacy_model = pickle.load(f)

            self.model = getattr(legacy_model, 'model', legacy_model)
            self.pipeline = None
            self.metadata = {
                'artifact_type': 'legacy_estimator_without_preprocessing',
                'model_name': self.model_name,
                'model_version': '1.0',
                'threshold': 0.5,
                'calibrated': False,
                'warning': 'Legacy estimator loaded without fitted preprocessing pipeline.',
            }
            loaded_path = model_path

        # Try to load regressor (optional)
        regressor_path = self.model_dir / "regression" / f"rf_regressor.pkl"
        if regressor_path.exists():
            try:
                with open(regressor_path, 'rb') as f:
                    self.regressor = pickle.load(f)
            except Exception as e:
                print(f"Warning: Could not load regressor: {e}")

        self.is_loaded = True
        print(f"[PredictionService] Loaded {self.model_name} model from {loaded_path}")

    def _prepare_features(self, twin_state: StudentTwinState) -> np.ndarray:
        """Extract raw features in production order for the pipeline."""
        from simulation.feature_recalculator import FeatureRecalculator

        features = FeatureRecalculator.extract_features(twin_state)
        if len(features) != EXPECTED_FEATURE_COUNT:
            raise ValueError(
                f"Expected {EXPECTED_FEATURE_COUNT} features, got {len(features)}. "
                "Feature extraction error."
            )
        return np.array(features, dtype=np.float32).reshape(1, -1)

    def _transform_features_for_test(self, twin_state: StudentTwinState) -> np.ndarray:
        """Expose the fitted preprocessing transform for regression tests."""
        if self.pipeline is None:
            raise RuntimeError("Production pipeline is not loaded")
        X = self._prepare_features(twin_state)
        return self.pipeline[:-1].transform(X)

    def predict(
        self,
        twin_state: StudentTwinState,
        day: int = 0
    ) -> PredictionSnapshot:
        """
        Predict overload probability and strain index from StudentTwinState.

        Args:
            twin_state: Student digital twin state at time t
            day: Semester day for context

        Returns:
            PredictionSnapshot with probability, prediction, strain, features
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call _load_models() first.")

        X = self._prepare_features(twin_state)

        # Get binary prediction
        predictor = self.pipeline if self.pipeline is not None else self.model
        y_pred_proba = predictor.predict_proba(X)  # [neg_prob, pos_prob]
        overload_prob = float(y_pred_proba[0, 1])
        overload_pred = bool(overload_prob >= self.threshold)

        # Get strain index (regression)
        strain_index = None
        if self.regressor is not None:
            try:
                strain_index = float(self.regressor.predict(X)[0])
            except Exception as e:
                print(f"Warning: Regression prediction failed: {e}")

        # Global RF importances, not a local explanation for this student/state.
        top_features = self._get_top_features(twin_state, 5)

        snapshot = PredictionSnapshot(
            overload_probability=overload_prob,
            overload_prediction=overload_pred,
            strain_index=strain_index,
            model_name=self.model_name,
            model_version="1.0",
            timestamp=datetime.now().isoformat(),
            day=day,
            top_contributing_features=top_features,
            confidence_info={
                'calibrated': self.calibrated,
                'calibration_method': self.metadata.get('calibration_method'),
                'calibration_note': self.metadata.get('calibration_note'),
                'num_features': EXPECTED_FEATURE_COUNT,
                'feature_order': self.feature_names,
                'threshold': self.threshold,
                'threshold_source': self.metadata.get('threshold_source'),
                'model_type': type(self.model).__name__,
                'artifact_type': self.metadata.get('artifact_type'),
                'feature_importance_scope': 'global_model_feature_importance',
                'local_explanation_available': False,
            },
        )

        return snapshot

    def _get_top_features(
        self,
        twin_state: StudentTwinState,
        top_k: int = 5
    ) -> Dict[str, float]:
        """
        Get global model feature importances.

        These describe the trained RF model overall; they are not local
        student-specific drivers for the current prediction.

        Args:
            twin_state: Student state
            top_k: Number of top features to return

        Returns:
            Dictionary of feature_name -> importance_score
        """
        # Extract raw features
        from simulation.feature_recalculator import FeatureRecalculator
        feature_names = FeatureRecalculator.get_feature_names()

        # Get model feature importance if available
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            top_indices = np.argsort(importances)[-top_k:][::-1]
            return {
                feature_names[i]: float(importances[i])
                for i in top_indices
            }

        # Fallback: return None
        return {}

    def get_model_info(self) -> Dict[str, Any]:
        """Get model metadata."""
        return {
            'model_name': self.model_name,
            'model_type': type(self.model).__name__,
            'is_loaded': self.is_loaded,
            'has_regressor': self.regressor is not None,
            'num_features': EXPECTED_FEATURE_COUNT,
            'feature_order': self.feature_names,
            'threshold': self.threshold,
            'threshold_source': self.metadata.get('threshold_source'),
            'calibrated': self.calibrated,
            'calibration_method': self.metadata.get('calibration_method'),
            'artifact_type': self.metadata.get('artifact_type'),
        }
