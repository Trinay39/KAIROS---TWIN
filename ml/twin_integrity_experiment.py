"""Twin integrity regeneration experiment for KAIROS-TWIN.

This module intentionally writes to an isolated experiment directory. It uses
the same Phase 3 feature/label/split logic and Phase 4 model classes as the
production pipeline, while preserving the existing production artifacts.
"""
from __future__ import annotations

import json
import pickle
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from core.leakage_tests import LeakageTests
from core.temporal_sampler import Sample
from ml.calibration import CalibrationAnalyzer
from ml.data_loader import DataLoader
from ml.evaluate import Evaluator
from ml.feature_contract import (
    EXPECTED_FEATURE_COUNT,
    prefixed_feature_order,
    raw_feature_order,
    validate_prefixed_feature_columns,
)
from ml.interpretability import FeatureImportance
from ml.models import BaselineLogistic, BaselineRandomForest, BaselineXGBoost
from ml.preprocessing import Preprocessor
from ml.train import ModelTrainer
from phase3_pipeline import Phase3Pipeline


EXPERIMENT_VERSION = "twin_integrity_fix_v1"
BASELINE_VERSION = "pre_twin_integrity_fix"
RANDOM_STATE = 42
PREVIOUS_CONSTANT_FEATURES = [
    "X_attendance_trend_7d",
    "X_grades_below_personal_mean_pct",
    "X_active_subjects_count",
    "X_break_rate_7d",
    "X_distraction_rate_7d",
    "X_focus_quality_7d_avg",
    "X_procrastination_index_7d",
    "X_recovery_score_7d",
    "X_pending_assignment_effort_hours",
    "X_submission_rate_14d",
    "X_submissions_on_time_pct_14d",
    "X_effort_study_gap_7d",
    "X_interaction_trend_7d",
    "X_interaction_engagement_score",
    "X_avg_confidence_7d",
    "X_is_exam_period",
    "X_recovery_confidence_coupling",
]
HARD_LEAKAGE_TESTS = [
    "feature_temporal_bounds",
    "no_label_in_features",
    "samples_temporal_separation",
    "no_student_leakage_temporal",
]


def json_ready(value: Any) -> Any:
    """Convert numpy/pandas values into JSON-safe primitives."""
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        if not np.isfinite(value):
            return None
        return float(value)
    if isinstance(value, (np.ndarray,)):
        return json_ready(value.tolist())
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if not isinstance(value, (list, tuple, dict, np.ndarray)):
        try:
            if pd.isna(value):
                return None
        except TypeError:
            pass
    return value


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_ready(payload), indent=2), encoding="utf-8")


def archive_current_artifacts(
    archive_root: Path = Path("experiments/archive"),
    results_dir: Path = Path("experiments/results"),
    phase3_dir: Path = Path("data/phase3"),
) -> Path:
    """Copy current production artifacts and Phase 3 CSVs into an archive."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_dir = archive_root / f"{BASELINE_VERSION}_{timestamp}"
    archive_dir.mkdir(parents=True, exist_ok=False)

    if results_dir.exists():
        shutil.copytree(results_dir, archive_dir / "results")
    if phase3_dir.exists():
        shutil.copytree(phase3_dir, archive_dir / "data_phase3")

    write_json(
        archive_dir / "manifest.json",
        {
            "archive_id": archive_dir.name,
            "created_at": datetime.now().isoformat(),
            "baseline_version": BASELINE_VERSION,
            "production_results_source": str(results_dir),
            "phase3_data_source": str(phase3_dir),
            "note": "Copy-only archive before Twin integrity feature regeneration experiment.",
        },
    )
    return archive_dir


def _hard_leakage_passed(leakage_results: dict[str, Any]) -> bool:
    tests = leakage_results.get("tests", {})
    return all(tests.get(name, {}).get("passed", False) for name in HARD_LEAKAGE_TESTS)


def regenerate_phase3_dataset(
    output_dir: Path,
    raw_csv: Path = Path("data/synthetic_student_daily.csv"),
) -> dict[str, Any]:
    """Regenerate Phase 3 data into an isolated output directory."""
    pipeline = Phase3Pipeline(phase2_csv=str(raw_csv), baseline_sleep=7.5)

    twin_states_by_day = pipeline._compute_twin_states()
    features_by_day = pipeline._extract_features(twin_states_by_day)
    labels_by_day = pipeline._compute_labels()
    students = sorted(pipeline.df_all["student_id"].unique())
    train_samples, val_samples, test_samples = pipeline.sampler.create_temporal_samples(
        features_by_day, labels_by_day, students
    )

    leakage_results = pipeline.leakage_tester.run_all_tests(
        train_samples, val_samples, test_samples
    )
    leakage_results["tests"]["no_student_leakage_student_split"][
        "applicability"
    ] = "not_applicable_to_temporal_split"
    leakage_results["hard_gate_tests"] = HARD_LEAKAGE_TESTS
    leakage_results["hard_gate_passed"] = _hard_leakage_passed(leakage_results)
    if not _hard_leakage_passed(leakage_results):
        raise RuntimeError(
            "Hard temporal leakage validation failed; experiment halted before training."
        )

    df_train = pipeline.sampler.to_dataframe(train_samples)
    df_val = pipeline.sampler.to_dataframe(val_samples)
    df_test = pipeline.sampler.to_dataframe(test_samples)
    for df in (df_train, df_val, df_test):
        feature_cols = [c for c in df.columns if c.startswith("X_")]
        validate_prefixed_feature_columns(feature_cols)
        df[prefixed_feature_order()] = df[prefixed_feature_order()].astype(float)

    output_dir.mkdir(parents=True, exist_ok=True)
    df_train.to_csv(output_dir / "train.csv", index=False)
    df_val.to_csv(output_dir / "val.csv", index=False)
    df_test.to_csv(output_dir / "test.csv", index=False)
    df_combined = pd.concat([df_train, df_val, df_test], ignore_index=True)
    df_combined.to_csv(output_dir / "combined.csv", index=False)

    phase3_report = pipeline._generate_report(
        train_samples,
        val_samples,
        test_samples,
        df_train,
        df_val,
        df_test,
        leakage_results,
    )
    return {
        "samples": {
            "train": len(train_samples),
            "val": len(val_samples),
            "test": len(test_samples),
            "total": len(train_samples) + len(val_samples) + len(test_samples),
        },
        "dataframes": {
            "train": df_train,
            "val": df_val,
            "test": df_test,
            "combined": df_combined,
        },
        "sample_objects": {
            "train": train_samples,
            "val": val_samples,
            "test": test_samples,
        },
        "leakage_results": leakage_results,
        "phase3_report": phase3_report,
    }


def feature_quality(df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    """Return feature quality statistics for every ML feature."""
    rows = []
    for col in feature_cols:
        series = pd.to_numeric(df[col], errors="coerce")
        unique_count = int(series.nunique(dropna=False))
        variance = float(series.var(ddof=0)) if len(series) else 0.0
        rows.append(
            {
                "feature": col,
                "missing_count": int(series.isna().sum()),
                "missing_pct": float(series.isna().mean()) if len(series) else 0.0,
                "unique_count": unique_count,
                "variance": variance,
                "is_constant": bool(unique_count <= 1 or np.isclose(variance, 0.0)),
                "min": float(series.min()) if not series.dropna().empty else None,
                "max": float(series.max()) if not series.dropna().empty else None,
                "mean": float(series.mean()) if not series.dropna().empty else None,
                "std": float(series.std(ddof=0)) if not series.dropna().empty else None,
            }
        )
    return pd.DataFrame(rows)


def label_distribution(df_by_split: dict[str, pd.DataFrame]) -> dict[str, Any]:
    result = {}
    for split, df in df_by_split.items():
        y = df["y_binary"].astype(bool)
        result[split] = {
            "samples": int(len(df)),
            "positive_count": int(y.sum()),
            "negative_count": int((~y).sum()),
            "positive_rate": float(y.mean()) if len(y) else 0.0,
        }
    return result


def numeric_distribution(df: pd.DataFrame, column: str) -> dict[str, Any]:
    series = pd.to_numeric(df[column], errors="coerce")
    return {
        "count": int(series.count()),
        "missing_count": int(series.isna().sum()),
        "min": float(series.min()),
        "max": float(series.max()),
        "mean": float(series.mean()),
        "std": float(series.std(ddof=0)),
        "p25": float(series.quantile(0.25)),
        "p50": float(series.quantile(0.50)),
        "p75": float(series.quantile(0.75)),
    }


def dataset_comparison(
    old_phase3_dir: Path,
    new_dataframes: dict[str, pd.DataFrame],
    report_dir: Path,
) -> dict[str, Any]:
    feature_cols = prefixed_feature_order()
    old_combined = pd.read_csv(old_phase3_dir / "combined.csv")
    new_combined = new_dataframes["combined"]

    old_quality = feature_quality(old_combined, feature_cols)
    new_quality = feature_quality(new_combined, feature_cols)
    old_quality.to_csv(report_dir / "old_feature_quality.csv", index=False)
    new_quality.to_csv(report_dir / "new_feature_quality.csv", index=False)

    old_constants = old_quality.loc[old_quality["is_constant"], "feature"].tolist()
    new_constants = new_quality.loc[new_quality["is_constant"], "feature"].tolist()
    previous_constant_status = {}
    for feature in PREVIOUS_CONSTANT_FEATURES:
        old_row = old_quality[old_quality["feature"] == feature].iloc[0].to_dict()
        new_row = new_quality[new_quality["feature"] == feature].iloc[0].to_dict()
        previous_constant_status[feature] = {
            "old_constant": bool(old_row["is_constant"]),
            "new_constant": bool(new_row["is_constant"]),
            "old_unique_count": int(old_row["unique_count"]),
            "new_unique_count": int(new_row["unique_count"]),
            "new_min": new_row["min"],
            "new_max": new_row["max"],
            "new_mean": new_row["mean"],
            "reason_if_still_constant": _constant_reason(feature),
        }

    return {
        "feature_contract": {
            "expected_feature_count": EXPECTED_FEATURE_COUNT,
            "actual_feature_count": len(feature_cols),
            "order_matches_contract": list(feature_cols) == prefixed_feature_order(),
        },
        "old_constants": old_constants,
        "new_constants": new_constants,
        "resolved_previous_constants": [
            f for f in PREVIOUS_CONSTANT_FEATURES if f in old_constants and f not in new_constants
        ],
        "newly_constant_features": [
            f for f in new_constants if f not in old_constants
        ],
        "still_constant_previous_features": [
            f for f in PREVIOUS_CONSTANT_FEATURES if f in new_constants
        ],
        "previous_constant_status": previous_constant_status,
        "stress_distribution": {
            "old_X_avg_stress_7d": numeric_distribution(old_combined, "X_avg_stress_7d"),
            "new_X_avg_stress_7d": numeric_distribution(new_combined, "X_avg_stress_7d"),
        },
        "label_distribution": {
            "old": label_distribution(
                {
                    "train": pd.read_csv(old_phase3_dir / "train.csv"),
                    "val": pd.read_csv(old_phase3_dir / "val.csv"),
                    "test": pd.read_csv(old_phase3_dir / "test.csv"),
                    "combined": old_combined,
                }
            ),
            "new": label_distribution(new_dataframes),
        },
        "semantic_checks": semantic_checks(new_combined),
    }


def _constant_reason(feature: str) -> str | None:
    reasons = {
        "X_active_subjects_count": "Raw CSV has no subject/course identifier; ML adapter preserves legacy value 4.",
        "X_break_rate_7d": "Raw CSV has no break-event column.",
        "X_distraction_rate_7d": "Raw CSV has no distraction-event column.",
        "X_focus_quality_7d_avg": "Raw CSV has no focus-quality column.",
        "X_procrastination_index_7d": "Raw CSV has no submission-timing column.",
        "X_pending_assignment_effort_hours": "Raw CSV has no assignment-effort-hours column.",
        "X_effort_study_gap_7d": "Raw CSV has no assignment-effort-hours column.",
        "X_avg_confidence_7d": "Raw CSV has no confidence column.",
        "X_is_exam_period": "Prediction days stop at day 83; exam period begins at day 85.",
        "X_recovery_confidence_coupling": "Confidence is unavailable, so this interaction remains neutral.",
        "X_avg_session_duration_7d": "Raw CSV has no study_sessions column; the integrity fix no longer invents session depth.",
    }
    return reasons.get(feature)


def semantic_checks(df: pd.DataFrame) -> dict[str, Any]:
    checks = {}
    bounded = {
        "X_avg_stress_7d": (1.0, 5.0),
        "X_recovery_score_7d": (0.0, 1.0),
        "X_interaction_engagement_score": (0.0, 1.0),
        "X_submission_rate_14d": (0.0, 1.0),
        "X_submissions_on_time_pct_14d": (0.0, 1.0),
        "X_grades_below_personal_mean_pct": (0.0, 1.0),
        "X_workload_pressure_score_7d": (0.0, 1.0),
    }
    for feature, (lower, upper) in bounded.items():
        series = pd.to_numeric(df[feature], errors="coerce")
        checks[feature] = {
            "within_expected_bounds": bool((series.dropna() >= lower).all() and (series.dropna() <= upper).all()),
            "min": float(series.min()),
            "max": float(series.max()),
            "unique_count": int(series.nunique(dropna=False)),
        }
    return checks


def old_model_summary(results_dir: Path = Path("experiments/results")) -> dict[str, Any]:
    summary = {}
    for model_name in ["logistic", "rf", "xgboost"]:
        path = results_dir / model_name / "metrics.json"
        if not path.exists():
            continue
        metrics = json.loads(path.read_text(encoding="utf-8"))
        summary[model_name] = {}
        for split in ["val", "test"]:
            if split not in metrics:
                continue
            summary[model_name][split] = {
                key: metrics[split].get(key)
                for key in [
                    "roc_auc",
                    "pr_auc",
                    "accuracy",
                    "precision",
                    "recall",
                    "f1",
                    "brier_score",
                    "threshold",
                    "confusion_matrix",
                    "sample_count",
                    "positive_count",
                    "negative_count",
                ]
            }
    metadata_path = results_dir / "metadata.json"
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        summary["production_metadata"] = {
            "production_model_name": metadata.get("production_model_name"),
            "production_threshold": metadata.get("production_threshold"),
            "production_threshold_source": metadata.get("production_threshold_source"),
            "optimal_threshold": metadata.get("optimal_threshold"),
            "optimal_threshold_model": metadata.get("optimal_threshold_model"),
            "calibrated": metadata.get("calibrated"),
        }
    return summary


def _model_importance(model_name: str, model: Any, feature_names: list[str]) -> dict[str, float]:
    if model_name == "logistic":
        return FeatureImportance.logistic_coefficients(model.model, feature_names)
    if hasattr(model.model, "feature_importances_"):
        return FeatureImportance.rf_importance(model.model, feature_names)
    return {}


def evaluate_model(
    model_name: str,
    model: Any,
    X: np.ndarray,
    y: np.ndarray,
    feature_names: list[str],
    threshold: float,
) -> dict[str, Any]:
    y_proba = model.predict_proba(X)[:, 1]
    metrics = Evaluator.compute_metrics(y, None, y_proba, threshold=threshold)
    metrics["importance"] = _model_importance(model_name, model, feature_names)
    metrics["calibration"] = CalibrationAnalyzer.compute_calibration_metrics(y, y_proba, n_bins=10)
    return metrics


def train_models(data_dir: Path, results_dir: Path) -> dict[str, Any]:
    """Train the same baseline model families and save candidate artifacts."""
    loader = DataLoader(
        str(data_dir / "train.csv"),
        str(data_dir / "val.csv"),
        str(data_dir / "test.csv"),
        verbose=True,
    )
    loader.load()
    validation = loader.validate()
    if not validation["all_passed"]:
        raise RuntimeError("Regenerated dataset failed DataLoader validation.")

    feature_names = loader.get_features()
    X_train, y_train, _ = loader.get_X_y("train")
    X_val, y_val, _ = loader.get_X_y("val")
    X_test, y_test, _ = loader.get_X_y("test")

    preprocessor = Preprocessor(method="standard", handle_missing=True, random_state=RANDOM_STATE)
    X_train_prep = preprocessor.fit_transform(X_train, feature_names=feature_names)
    X_val_prep = preprocessor.transform(X_val)
    X_test_prep = preprocessor.transform(X_test)

    trainer = ModelTrainer(random_state=RANDOM_STATE)
    hyperparams: dict[str, Any] = {}
    cv_results: dict[str, Any] = {}
    models: dict[str, Any] = {}

    lr_params, lr_cv = trainer.tune_logistic(X_train_prep, y_train)
    hyperparams["logistic"] = lr_params
    cv_results["logistic"] = lr_cv
    models["logistic"] = BaselineLogistic(**lr_params, random_state=RANDOM_STATE).fit(
        X_train_prep, y_train
    )

    rf_params, rf_cv = trainer.tune_random_forest(X_train_prep, y_train)
    hyperparams["rf"] = rf_params
    cv_results["rf"] = rf_cv
    models["rf"] = BaselineRandomForest(**rf_params, random_state=RANDOM_STATE).fit(
        X_train_prep, y_train
    )

    try:
        xgb_params, xgb_cv = trainer.tune_xgboost(X_train_prep, y_train)
        hyperparams["xgboost"] = xgb_params
        cv_results["xgboost"] = xgb_cv
        if xgb_params:
            models["xgboost"] = BaselineXGBoost(
                **xgb_params, random_state=RANDOM_STATE
            ).fit(X_train_prep, y_train)
    except Exception as exc:
        hyperparams["xgboost"] = {}
        cv_results["xgboost"] = {"available": False, "reason": str(exc)}

    results: dict[str, Any] = {}
    threshold_report: dict[str, Any] = {}
    for model_name, model in models.items():
        y_val_proba = model.predict_proba(X_val_prep)[:, 1]
        threshold, threshold_metrics = Evaluator.find_optimal_threshold(
            y_val, y_val_proba, metric="f1"
        )
        threshold_report[model_name] = {
            "threshold": float(threshold),
            "source": "validation_f1_grid_0.10_0.90_step_0.01",
            "validation_f1_at_threshold": threshold_metrics["f1"],
        }
        results[model_name] = {
            "val": evaluate_model(
                model_name, model, X_val_prep, y_val, feature_names, threshold
            ),
            "test": evaluate_model(
                model_name, model, X_test_prep, y_test, feature_names, threshold
            ),
        }

    selected_model_name = select_model(results)
    selected_model = models[selected_model_name]
    selected_threshold = threshold_report[selected_model_name]["threshold"]
    suitable = candidate_is_suitable(results[selected_model_name]["test"])

    results_dir.mkdir(parents=True, exist_ok=True)
    for model_name, model in models.items():
        with (results_dir / f"{model_name}.pkl").open("wb") as f:
            pickle.dump(model, f)
        model_dir = results_dir / model_name
        model_dir.mkdir(exist_ok=True)
        write_json(model_dir / "metrics.json", results[model_name])

    candidate_artifact_path = None
    if suitable:
        production_pipeline = Pipeline(
            [
                ("imputer", preprocessor.imputer),
                ("scaler", preprocessor.scaler),
                ("classifier", selected_model.model),
            ]
        )
        candidate_artifact = {
            "artifact_type": "kairos_twin_candidate_pipeline",
            "artifact_version": EXPERIMENT_VERSION,
            "candidate_only": True,
            "promoted_to_production": False,
            "model_name": selected_model_name,
            "model_version": EXPERIMENT_VERSION,
            "pipeline": production_pipeline,
            "feature_names": feature_names,
            "raw_feature_names": raw_feature_order(),
            "feature_count": len(feature_names),
            "threshold": float(selected_threshold),
            "threshold_source": threshold_report[selected_model_name]["source"],
            "threshold_metric": "validation_f1",
            "calibrated": False,
            "calibration_method": None,
            "calibration_note": "Calibration was analyzed only; no calibrator is trained or applied in this candidate.",
            "random_state": RANDOM_STATE,
            "experiment_version": EXPERIMENT_VERSION,
            "baseline_version": BASELINE_VERSION,
            "training_data": {
                "train_path": str(data_dir / "train.csv"),
                "val_path": str(data_dir / "val.csv"),
                "test_path": str(data_dir / "test.csv"),
            },
            "preprocessing": {
                "imputer": "SimpleImputer(strategy=mean)",
                "scaler": "StandardScaler",
                "fit_scope": "train_split_only",
            },
        }
        candidate_artifact_path = results_dir / "candidate_model_pipeline.pkl"
        with candidate_artifact_path.open("wb") as f:
            pickle.dump(candidate_artifact, f)

    metadata = {
        "experiment_version": EXPERIMENT_VERSION,
        "baseline_version": BASELINE_VERSION,
        "timestamp": datetime.now().isoformat(),
        "random_state": RANDOM_STATE,
        "cv_strategy": "TimeSeriesSplit(n_splits=5)",
        "model_selection": {
            "selected_model_name": selected_model_name,
            "criterion": "highest_validation_roc_auc_then_pr_auc_then_f1",
            "candidate_suitable": suitable,
            "candidate_artifact": (
                str(candidate_artifact_path) if candidate_artifact_path is not None else None
            ),
            "candidate_only": True,
            "promoted_to_production": False,
        },
        "thresholds": threshold_report,
        "feature_count": len(feature_names),
        "feature_names": feature_names,
        "raw_feature_names": raw_feature_order(),
        "hyperparams": hyperparams,
        "cv_results": cv_results,
        "preprocessing": {
            "imputer": "SimpleImputer(strategy=mean)",
            "scaler": "StandardScaler",
            "fit_scope": "train_split_only",
            "scaler_mean": preprocessor.get_scaler_params()["mean"].tolist(),
            "scaler_scale": preprocessor.get_scaler_params()["scale"].tolist(),
            "scaler_var": preprocessor.get_scaler_params()["var"].tolist(),
        },
        "training_data": {
            "train_path": str(data_dir / "train.csv"),
            "val_path": str(data_dir / "val.csv"),
            "test_path": str(data_dir / "test.csv"),
        },
    }
    write_json(results_dir / "metadata.json", metadata)

    return {
        "validation": validation,
        "metadata": metadata,
        "results": results,
        "models": models,
    }


def select_model(results: dict[str, Any]) -> str:
    """Select by validation ROC-AUC, using PR-AUC then F1 as tie-breakers."""
    ranking = sorted(
        results,
        key=lambda name: (
            results[name]["val"]["roc_auc"],
            results[name]["val"]["pr_auc"],
            results[name]["val"]["f1"],
        ),
        reverse=True,
    )
    return ranking[0]


def candidate_is_suitable(test_metrics: dict[str, Any]) -> bool:
    """Minimal sanity gate for writing a candidate artifact."""
    return bool(
        test_metrics["roc_auc"] >= 0.75
        and test_metrics["pr_auc"] >= 0.70
        and test_metrics["brier_score"] <= 0.25
    )


def compact_metric_summary(results: dict[str, Any]) -> dict[str, Any]:
    compact = {}
    for model_name, splits in results.items():
        compact[model_name] = {}
        for split, metrics in splits.items():
            compact[model_name][split] = {
                key: metrics.get(key)
                for key in [
                    "roc_auc",
                    "pr_auc",
                    "accuracy",
                    "precision",
                    "recall",
                    "specificity",
                    "f1",
                    "brier_score",
                    "threshold",
                    "confusion_matrix",
                    "sample_count",
                    "positive_count",
                    "negative_count",
                ]
            }
            if "calibration" in metrics:
                compact[model_name][split]["calibration"] = {
                    key: metrics["calibration"].get(key)
                    for key in ["ece", "mce", "brier"]
                }
    return compact


def run_twin_integrity_experiment(
    experiment_root: Path = Path("experiments/twin_integrity_fix"),
    create_archive: bool = True,
    existing_archive_dir: Path | None = None,
) -> dict[str, Any]:
    """Run the complete isolated regeneration and candidate-training experiment."""
    archive_dir = existing_archive_dir
    if archive_dir is None and create_archive:
        archive_dir = archive_current_artifacts()

    data_dir = experiment_root / "data_phase3"
    results_dir = experiment_root / "results"
    reports_dir = experiment_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    phase3 = regenerate_phase3_dataset(data_dir)
    write_json(reports_dir / "phase3_report.json", phase3["phase3_report"])
    write_json(reports_dir / "leakage_results.json", phase3["leakage_results"])

    comparison = dataset_comparison(
        Path("data/phase3"), phase3["dataframes"], reports_dir
    )
    write_json(reports_dir / "dataset_comparison.json", comparison)

    training = train_models(data_dir, results_dir)
    old_metrics = old_model_summary()
    metric_summary = {
        "old": old_metrics,
        "new": compact_metric_summary(training["results"]),
    }
    write_json(reports_dir / "model_metric_comparison.json", metric_summary)

    final_report = {
        "experiment_version": EXPERIMENT_VERSION,
        "baseline_version": BASELINE_VERSION,
        "created_at": datetime.now().isoformat(),
        "archive_dir": str(archive_dir) if archive_dir else None,
        "experiment_root": str(experiment_root),
        "production_artifacts_modified": False,
        "raw_data_modified": False,
        "hard_leakage_passed": _hard_leakage_passed(phase3["leakage_results"]),
        "label_distribution_warning_passed": phase3["leakage_results"]["tests"]
        .get("label_distribution", {})
        .get("passed"),
        "dataset_comparison": comparison,
        "model_metrics": metric_summary,
        "candidate_metadata": training["metadata"],
    }
    write_json(experiment_root / "final_report.json", final_report)
    write_markdown_report(experiment_root / "REPORT.md", final_report)
    return final_report


def write_markdown_report(path: Path, report: dict[str, Any]) -> None:
    selected = report["candidate_metadata"]["model_selection"]["selected_model_name"]
    candidate = report["candidate_metadata"]["model_selection"]
    new_metrics = report["model_metrics"]["new"]
    lines = [
        "# KAIROS-TWIN Twin Integrity ML Experiment",
        "",
        f"- Experiment version: `{report['experiment_version']}`",
        f"- Baseline archive: `{report['archive_dir']}`",
        f"- Production artifacts modified: `{report['production_artifacts_modified']}`",
        f"- Hard leakage checks passed: `{report['hard_leakage_passed']}`",
        f"- Candidate model: `{selected}`",
        f"- Candidate suitable: `{candidate['candidate_suitable']}`",
        f"- Candidate artifact: `{candidate['candidate_artifact']}`",
        "",
        "## New Test Metrics",
        "",
        "| Model | ROC-AUC | PR-AUC | Accuracy | Precision | Recall | F1 | Brier | Threshold |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for model_name, metrics in new_metrics.items():
        test = metrics["test"]
        lines.append(
            "| {name} | {roc:.4f} | {pr:.4f} | {acc:.4f} | {prec:.4f} | {rec:.4f} | {f1:.4f} | {brier:.4f} | {thr:.2f} |".format(
                name=model_name,
                roc=test["roc_auc"],
                pr=test["pr_auc"],
                acc=test["accuracy"],
                prec=test["precision"],
                rec=test["recall"],
                f1=test["f1"],
                brier=test["brier_score"],
                thr=test["threshold"],
            )
        )
    lines.extend(
        [
            "",
            "## Feature Quality",
            "",
            f"- Previous constant features resolved: `{report['dataset_comparison']['resolved_previous_constants']}`",
            f"- Previous features still constant: `{report['dataset_comparison']['still_constant_previous_features']}`",
            f"- Newly constant features: `{report['dataset_comparison']['newly_constant_features']}`",
            "- Full quality tables: `reports/old_feature_quality.csv`, `reports/new_feature_quality.csv`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
