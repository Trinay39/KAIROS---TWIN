"""Artifact-level checks for the Twin integrity ML regeneration experiment."""
from __future__ import annotations

import json
import pickle
from pathlib import Path

import pandas as pd
import pytest

from ml.feature_contract import prefixed_feature_order, raw_feature_order


EXPERIMENT_ROOT = Path("experiments/twin_integrity_fix")
FINAL_REPORT = EXPERIMENT_ROOT / "final_report.json"


def _load_final_report() -> dict:
    if not FINAL_REPORT.exists():
        pytest.skip("Twin integrity experiment artifacts have not been generated.")
    return json.loads(FINAL_REPORT.read_text(encoding="utf-8"))


def test_twin_integrity_experiment_preserves_production_artifacts():
    report = _load_final_report()
    candidate = report["candidate_metadata"]["model_selection"]

    assert report["production_artifacts_modified"] is False
    assert report["raw_data_modified"] is False
    assert report["archive_dir"]
    assert Path(report["archive_dir"]).exists()
    assert candidate["candidate_only"] is True
    assert candidate["promoted_to_production"] is False
    assert candidate["candidate_artifact"] != "experiments/results/model_pipeline.pkl"


def test_twin_integrity_candidate_artifact_has_truthful_metadata():
    report = _load_final_report()
    metadata = report["candidate_metadata"]
    candidate = metadata["model_selection"]
    artifact_path = Path(candidate["candidate_artifact"])

    assert artifact_path.exists()
    with artifact_path.open("rb") as f:
        artifact = pickle.load(f)

    selected_model = candidate["selected_model_name"]
    assert artifact["artifact_type"] == "kairos_twin_candidate_pipeline"
    assert artifact["candidate_only"] is True
    assert artifact["promoted_to_production"] is False
    assert artifact["experiment_version"] == "twin_integrity_fix_v1"
    assert artifact["model_name"] == selected_model
    assert artifact["feature_count"] == 46
    assert artifact["feature_names"] == prefixed_feature_order()
    assert artifact["raw_feature_names"] == raw_feature_order()
    assert artifact["threshold"] == pytest.approx(
        metadata["thresholds"][selected_model]["threshold"]
    )
    assert artifact["threshold_source"] == "validation_f1_grid_0.10_0.90_step_0.01"
    assert artifact["calibrated"] is False


def test_twin_integrity_report_records_hard_leakage_gate_and_split_scope():
    report = _load_final_report()
    leakage_path = EXPERIMENT_ROOT / "reports" / "leakage_results.json"
    leakage = json.loads(leakage_path.read_text(encoding="utf-8"))

    assert report["hard_leakage_passed"] is True
    assert leakage["hard_gate_passed"] is True
    assert leakage["hard_gate_tests"] == [
        "feature_temporal_bounds",
        "no_label_in_features",
        "samples_temporal_separation",
        "no_student_leakage_temporal",
    ]
    assert (
        leakage["tests"]["no_student_leakage_student_split"]["applicability"]
        == "not_applicable_to_temporal_split"
    )


def test_twin_integrity_feature_quality_resolves_supported_constants():
    report = _load_final_report()
    comparison = report["dataset_comparison"]
    expected_resolved = {
        "X_attendance_trend_7d",
        "X_grades_below_personal_mean_pct",
        "X_recovery_score_7d",
        "X_submission_rate_14d",
        "X_submissions_on_time_pct_14d",
        "X_interaction_trend_7d",
        "X_interaction_engagement_score",
    }
    still_constant = set(comparison["still_constant_previous_features"])

    assert expected_resolved.issubset(set(comparison["resolved_previous_constants"]))
    assert "X_recovery_confidence_coupling" in still_constant
    assert comparison["newly_constant_features"] == ["X_avg_session_duration_7d"]
    assert comparison["previous_constant_status"]["X_recovery_confidence_coupling"][
        "reason_if_still_constant"
    ]
    assert comparison["feature_contract"]["order_matches_contract"] is True

    quality = pd.read_csv(EXPERIMENT_ROOT / "reports" / "new_feature_quality.csv")
    assert len(quality) == 46
    assert quality["missing_count"].sum() == 0
    for feature in expected_resolved:
        row = quality[quality["feature"] == feature].iloc[0]
        assert bool(row["is_constant"]) is False
        assert int(row["unique_count"]) > 1


def test_twin_integrity_semantic_checks_and_thresholds_are_model_specific():
    report = _load_final_report()
    comparison = report["dataset_comparison"]
    metadata = report["candidate_metadata"]
    selected_model = metadata["model_selection"]["selected_model_name"]

    assert all(
        check["within_expected_bounds"]
        for check in comparison["semantic_checks"].values()
    )
    for model_name, threshold in metadata["thresholds"].items():
        assert threshold["source"] == "validation_f1_grid_0.10_0.90_step_0.01"
        assert 0.1 <= threshold["threshold"] <= 0.9
    assert report["model_metrics"]["new"][selected_model]["test"]["threshold"] == pytest.approx(
        metadata["thresholds"][selected_model]["threshold"]
    )
