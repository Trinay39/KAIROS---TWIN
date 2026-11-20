"""Production ML serving tests for preprocessing and feature-order integrity."""
from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pytest

from core.schemas import (
    AcademicState,
    BehavioralState,
    EngagementState,
    HistorySummary,
    PredictionSnapshot,
    RecoveryState,
    StudentTwinState,
    TemporalContext,
    WorkloadState,
)
from ml.data_loader import DataLoader
from ml.feature_contract import (
    FeatureContractError,
    raw_feature_order,
    raw_mapping_to_array,
    validate_raw_feature_mapping,
)
from ml.preprocessing import Preprocessor
from simulation.feature_recalculator import FeatureRecalculator
from simulation.prediction_service import PredictionService


ARTIFACT_PATH = Path("experiments/results/model_pipeline.pkl")
METADATA_PATH = Path("experiments/results/metadata.json")


@pytest.fixture(scope="module")
def production_artifact():
    with ARTIFACT_PATH.open("rb") as f:
        return pickle.load(f)


@pytest.fixture(scope="module")
def production_metadata():
    return json.loads(METADATA_PATH.read_text())


@pytest.fixture(scope="module")
def loader():
    data_loader = DataLoader(
        "data/phase3/train.csv",
        "data/phase3/val.csv",
        "data/phase3/test.csv",
        verbose=False,
    )
    data_loader.load()
    validation = data_loader.validate()
    assert validation["all_passed"], validation
    return data_loader


def known_high_risk_state() -> StudentTwinState:
    return StudentTwinState(
        student_id="PROD_TEST_001",
        day=50,
        academic=AcademicState(
            attendance_rate_7d=0.70,
            grade_trend_30d=-0.05,
            missed_deadlines_14d=4,
            academic_load_score=0.90,
        ),
        behavioral=BehavioralState(
            avg_study_hours_7d=2.0,
            study_consistency_score=0.35,
            procrastination_index_7d=0.85,
        ),
        recovery=RecoveryState(
            avg_sleep_hours_7d=5.2,
            sleep_deficit_7d_hours=15.0,
            recovery_score_7d=0.25,
        ),
        workload=WorkloadState(
            pending_assignment_count=14,
            deadline_density_next_7_known=7,
            deadline_density_trend_7d=0.8,
            workload_pressure_score_7d=0.95,
        ),
        engagement=EngagementState(avg_stress_7d=4.6, avg_confidence_7d=1.5),
        temporal=TemporalContext(
            day_of_semester=50,
            week_of_semester=8,
            day_of_week=0,
            is_exam_period=False,
            is_midterm_period=False,
            semester_phase="mid",
            days_until_exam_period=35,
        ),
        predictions=PredictionSnapshot(),
        history=HistorySummary(),
    )


def test_training_and_inference_preprocessing_are_equivalent(loader, production_artifact):
    X_train, _, _ = loader.get_X_y("train")
    training_preprocessor = Preprocessor(method="standard", handle_missing=True)
    expected = training_preprocessor.fit_transform(
        X_train,
        feature_names=loader.get_features(),
    )[0:1]

    actual = production_artifact["pipeline"][:-1].transform(X_train[0:1])

    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-6)


def test_inference_feature_order_is_deterministic(production_artifact):
    expected = raw_feature_order()

    assert FeatureRecalculator.get_feature_names() == expected
    assert production_artifact["raw_feature_names"] == expected
    assert raw_mapping_to_array({name: idx for idx, name in enumerate(expected)}).shape == (1, 46)


def test_missing_required_feature_raises_clear_error():
    features = {name: 0.0 for name in raw_feature_order()}
    missing_name = raw_feature_order()[0]
    del features[missing_name]

    with pytest.raises(FeatureContractError, match="missing required features"):
        validate_raw_feature_mapping(features)


def test_unexpected_feature_raises_clear_error():
    features = {name: 0.0 for name in raw_feature_order()}
    features["unexpected_demo_feature"] = 1.0

    with pytest.raises(FeatureContractError, match="unexpected features"):
        validate_raw_feature_mapping(features)


def test_saved_production_artifact_loads_successfully(production_artifact):
    assert production_artifact["artifact_type"] == "kairos_twin_production_pipeline"
    assert production_artifact["pipeline"].named_steps["imputer"] is not None
    assert production_artifact["pipeline"].named_steps["scaler"] is not None
    assert production_artifact["pipeline"].named_steps["classifier"] is not None
    assert (
        type(production_artifact["pipeline"].named_steps["classifier"]).__name__
        == "RandomForestClassifier"
    )
    assert production_artifact["model_name"] == "rf"
    assert production_artifact["feature_count"] == 46


def test_known_sample_probability_is_deterministic():
    service = PredictionService()
    snapshot = service.predict(known_high_risk_state(), day=50)

    assert 0.0 <= snapshot.overload_probability <= 1.0
    assert snapshot.overload_probability == pytest.approx(0.7161453836232516, abs=1e-12)
    assert snapshot.overload_prediction is True


def test_inference_path_uses_pipeline_not_raw_classifier_directly():
    service = PredictionService()
    state = known_high_risk_state()
    raw_features = service._prepare_features(state)

    pipeline_probability = service.pipeline.predict_proba(raw_features)[0, 1]
    service_probability = service.predict(state, day=50).overload_probability
    raw_classifier_probability = service.model.predict_proba(raw_features)[0, 1]

    assert service_probability == pytest.approx(pipeline_probability, abs=1e-12)
    assert raw_classifier_probability != pytest.approx(service_probability, abs=1e-6)


def test_calibration_metadata_matches_reality(production_artifact, production_metadata):
    service = PredictionService()
    snapshot = service.predict(known_high_risk_state(), day=50)

    assert production_artifact["calibrated"] is False
    assert production_metadata["calibrated"] is False
    assert service.get_model_info()["calibrated"] is False
    assert snapshot.confidence_info["calibrated"] is False
    assert production_artifact["calibration_method"] is None
    assert production_metadata["calibration_method"] is None
    assert "no calibrator is trained or applied" in production_artifact["calibration_note"]


def test_production_threshold_belongs_to_served_model(production_artifact, production_metadata):
    service = PredictionService()

    assert production_artifact["model_name"] == "rf"
    assert production_metadata["production_model_name"] == "rf"
    assert service.model_name == "rf"
    assert service.threshold == pytest.approx(0.5)
    assert production_artifact["threshold"] == pytest.approx(service.threshold)
    assert production_metadata["production_threshold"] == pytest.approx(service.threshold)
    assert production_artifact["threshold_source"] == "fixed_default_for_served_rf_model"
    assert production_metadata["production_threshold_source"] == production_artifact["threshold_source"]


def test_production_metadata_feature_contract_and_preprocessing_are_truthful(
    production_artifact,
    production_metadata,
):
    service = PredictionService()

    assert production_metadata["feature_count"] == 46
    assert production_metadata["feature_names"] == production_artifact["feature_names"]
    assert production_metadata["raw_feature_names"] == raw_feature_order()
    assert service.get_model_info()["feature_order"] == raw_feature_order()
    assert production_artifact["preprocessing"] == {
        "imputer": "SimpleImputer(strategy=mean)",
        "scaler": "StandardScaler",
        "fit_scope": "train_split_only",
    }
    assert production_metadata["preprocessing"]["fit_scope"] == "train_split_only"
