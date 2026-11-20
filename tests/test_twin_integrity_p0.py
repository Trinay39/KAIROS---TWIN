"""P0 integrity tests for stress scale, provenance, and honest twin fields."""
from __future__ import annotations

from copy import deepcopy

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from api.persistence import Phase7Persistence
from api.service import Phase7Service
from core.feature_engine import FeatureEngine
from core.schemas import StudentTwinState
from core.twin_engine import TwinEngine
from ml.feature_contract import raw_feature_order
from simulation.counterfactual_engine import CounterfactualEngine
from simulation.prediction_service import PredictionService
from simulation.scenario_schema import create_increase_sleep_scenario


API_KEY = "twin-integrity-test-key"
VALID_PROVENANCE_TYPES = {
    "observed",
    "derived",
    "imputed_default",
    "hardcoded",
    "predicted",
}


@pytest.fixture
def service(tmp_path):
    persistence = Phase7Persistence(base_dir=str(tmp_path / "data" / "phase7"))
    return Phase7Service(persistence=persistence)


@pytest.fixture
def client(service):
    app = create_app(service=service, api_key=API_KEY)
    with TestClient(app) as test_client:
        yield test_client


def headers():
    return {"Authorization": f"Bearer {API_KEY}"}


def base_rows(day_count=7, stress=0.5, include_load=True, include_recovery=True):
    rows = []
    for day in range(1, day_count + 1):
        row = {
            "student_id": "STU_P0",
            "day": day,
            "study_hours": 4.0,
            "sleep_hours": 7.0,
            "stress_level": stress,
            "grade": 80.0,
            "attendance_rate": 0.8 + day * 0.01,
            "missed_deadline_observed": 0,
        }
        if include_load:
            row.update({
                "workload_pressure": 0.7,
                "pending_assignments": 5,
                "upcoming_deadlines_7d": 2,
                "assignment_due_today": 1 if day in {3, 6} else 0,
            })
        if include_recovery:
            row["recovery_index"] = 0.6 + day * 0.02
        rows.append(row)
    return rows


def test_api_stress_level_normalizes_zero_five_ten(service):
    for external, internal in [(0, 0.0), (5, 0.5), (10, 1.0)]:
        adapted = service._adapt_observations([
            {
                "day": 1,
                "study_hours": 4.0,
                "sleep_hours": 7.0,
                "stress_level": external,
                "grade": 80,
            }
        ])
        assert adapted[0]["stress_level"] == pytest.approx(internal)


@pytest.mark.parametrize("bad_value", [-0.1, 10.1, float("nan"), float("inf")])
def test_api_stress_level_rejects_invalid_values(service, bad_value):
    with pytest.raises(ValueError):
        service._adapt_observations([
            {
                "day": 1,
                "study_hours": 4.0,
                "sleep_hours": 7.0,
                "stress_level": bad_value,
                "grade": 80,
            }
        ])


def test_api_stress_normalization_end_to_end_and_no_double_conversion(client):
    response = client.post(
        "/states/compute",
        headers=headers(),
        json={
            "student_id": "STU_P0",
            "day": 7,
            "observations": [
                {**row, "stress_level": 5.0}
                for row in base_rows(stress=0.5, include_load=False)
            ],
        },
    )
    assert response.status_code == 200, response.text
    state = response.json()
    assert state["raw_latest"]["stress_level"] == pytest.approx(0.5)
    assert state["engagement"]["avg_stress_7d"] == pytest.approx(3.0)

    internal_state = TwinEngine().compute_state(
        "STU_P0",
        7,
        pd.DataFrame(base_rows(stress=0.5, include_load=False)),
    )
    assert state["engagement"]["avg_stress_7d"] == pytest.approx(
        internal_state.engagement.avg_stress_7d
    )
    assert FeatureEngine().extract_features(internal_state)["avg_stress_7d"] == pytest.approx(3.0)


def test_twin_engine_rejects_non_internal_stress_scale():
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        TwinEngine().compute_state(
            "STU_P0",
            7,
            pd.DataFrame(base_rows(stress=5.0, include_load=False)),
        )


def test_important_fields_have_valid_provenance_classification():
    state = TwinEngine().compute_state("STU_P0", 7, pd.DataFrame(base_rows()))
    important_paths = [
        "academic.active_subjects_count",
        "academic.academic_load_score",
        "academic.attendance_trend_7d",
        "academic.grades_below_personal_mean_pct",
        "behavioral.avg_session_duration_7d",
        "recovery.recovery_score_7d",
        "workload.pending_assignment_effort_hours",
        "workload.submission_rate_14d",
        "workload.submissions_on_time_pct_14d",
        "workload.effort_study_gap_7d",
        "engagement.interaction_trend_7d",
        "engagement.interaction_engagement_score",
        "engagement.avg_confidence_7d",
        "engagement.engagement_composite_score",
    ]
    for path in important_paths:
        assert path in state.provenance
        assert state.provenance[path].type in VALID_PROVENANCE_TYPES


def test_active_subjects_not_faked_in_state_but_preserved_for_ml_adapter():
    state = TwinEngine().compute_state("STU_P0", 7, pd.DataFrame(base_rows(include_load=False)))
    assert state.academic.active_subjects_count == 0
    assert state.provenance["academic.active_subjects_count"].type == "imputed_default"
    assert state.provenance["academic.active_subjects_count"].imputed is True
    assert FeatureEngine().extract_features(state)["active_subjects_count"] == 4.0


def test_academic_load_score_is_derived_only_when_inputs_exist():
    state = TwinEngine().compute_state("STU_P0", 7, pd.DataFrame(base_rows()))
    expected = (0.7 + 0.5 + (2 / 7)) / 3
    assert state.academic.academic_load_score == pytest.approx(expected)
    assert state.provenance["academic.academic_load_score"].type == "derived"

    unavailable = TwinEngine().compute_state(
        "STU_P0",
        7,
        pd.DataFrame(base_rows(include_load=False)),
    )
    assert unavailable.academic.academic_load_score is None
    assert unavailable.provenance["academic.academic_load_score"].type == "imputed_default"


def test_recovery_score_uses_recovery_index_when_available():
    state = TwinEngine().compute_state("STU_P0", 7, pd.DataFrame(base_rows()))
    assert state.recovery.recovery_score_7d == pytest.approx(0.68)
    assert state.provenance["recovery.recovery_score_7d"].type == "derived"


def test_recovery_score_uses_sleep_formula_when_recovery_index_unavailable():
    state = TwinEngine().compute_state(
        "STU_P0",
        7,
        pd.DataFrame(base_rows(include_recovery=False)),
    )
    assert state.recovery.recovery_score_7d is not None
    assert 0.0 <= state.recovery.recovery_score_7d <= 1.0


def test_attendance_trend_is_real_ols_slope():
    state = TwinEngine().compute_state("STU_P0", 7, pd.DataFrame(base_rows()))
    assert state.academic.attendance_trend_7d == pytest.approx(0.01)


def test_grade_personal_baseline_uses_only_history_up_to_day():
    rows = base_rows(day_count=11, include_load=False)
    for idx, grade in enumerate([80, 80, 80, 80, 80, 70, 70, 90, 90, 70, 100]):
        rows[idx]["grade"] = grade
    state = TwinEngine().compute_state("STU_P0", 10, pd.DataFrame(rows))
    assert state.academic.grades_below_personal_mean_pct == pytest.approx(0.6)


def test_session_duration_unavailable_without_session_level_data():
    state = TwinEngine().compute_state("STU_P0", 7, pd.DataFrame(base_rows()))
    assert state.behavioral.avg_session_duration_7d is None
    assert state.provenance["behavioral.avg_session_duration_7d"].type == "imputed_default"


def test_feature_contract_order_remains_unchanged():
    assert raw_feature_order() == FeatureEngine.FEATURE_NAMES
    assert len(raw_feature_order()) == 46


def test_known_default_features_remain_constant_in_frozen_phase3_dataset():
    df = pd.read_csv("data/phase3/combined.csv")
    default_only = [
        "X_break_rate_7d",
        "X_distraction_rate_7d",
        "X_focus_quality_7d_avg",
        "X_procrastination_index_7d",
        "X_pending_assignment_effort_hours",
        "X_avg_confidence_7d",
    ]
    for column in default_only:
        assert df[column].nunique() == 1


def test_counterfactual_simulation_does_not_mutate_original_state():
    state = TwinEngine().compute_state("STU_P0", 7, pd.DataFrame(base_rows()))
    before = deepcopy(state.to_dict())
    engine = CounterfactualEngine(PredictionService())
    engine.simulate(state, create_increase_sleep_scenario(8.0, 7), day=7)
    assert state.to_dict() == before


def test_prediction_exposes_global_importance_not_local_explanation():
    state = TwinEngine().compute_state("STU_P0", 7, pd.DataFrame(base_rows()))
    snapshot = PredictionService().predict(state, day=7)
    assert snapshot.top_contributing_features
    assert snapshot.confidence_info["feature_importance_scope"] == "global_model_feature_importance"
    assert snapshot.confidence_info["local_explanation_available"] is False
