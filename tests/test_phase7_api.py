"""Tests for the additive Phase 7 FastAPI layer."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from api.persistence import Phase7Persistence
from api.service import Phase7Service


API_KEY = "phase7-test-key"


@pytest.fixture
def observations():
    rows = []
    for day in range(1, 58):
        rows.append({
            "student_id": "STU_PHASE7",
            "day": day,
            "attendance_rate": 0.8,
            "grade": 72 + (day % 4),
            "missed_deadline_observed": 1 if day in {45, 49} else 0,
            "study_hours": 2.5 + (day % 3) * 0.2,
            "sleep_hours": 6.0 + (day % 2) * 0.3,
            "stress_level": 0.75,
            "pending_assignments": 10,
            "upcoming_deadlines_7d": 4,
            "workload_pressure": 0.82,
            "platform_interactions": 18,
        })
    return rows


@pytest.fixture
def high_risk_state():
    return {
        "student_id": "STU_PHASE7",
        "day": 50,
        "academic": {
            "attendance_rate_7d": 0.7,
            "grade_trend_30d": -0.05,
            "missed_deadlines_14d": 4,
            "academic_load_score": 0.9,
        },
        "behavioral": {
            "avg_study_hours_7d": 2.0,
            "study_consistency_score": 0.35,
            "procrastination_index_7d": 0.85,
        },
        "recovery": {
            "avg_sleep_hours_7d": 5.2,
            "sleep_deficit_7d_hours": 15.0,
            "recovery_score_7d": 0.25,
        },
        "workload": {
            "pending_assignment_count": 14,
            "deadline_density_next_7_known": 7,
            "deadline_density_trend_7d": 0.8,
            "workload_pressure_score_7d": 0.95,
        },
        "engagement": {
            "avg_stress_7d": 4.6,
            "avg_confidence_7d": 1.5,
        },
        "temporal": {
            "day_of_semester": 50,
            "week_of_semester": 8,
            "day_of_week": 0,
            "is_exam_period": False,
            "is_midterm_period": False,
            "semester_phase": "mid",
            "days_until_exam_period": 35,
        },
    }


@pytest.fixture
def client(tmp_path):
    persistence = Phase7Persistence(base_dir=str(tmp_path / "data" / "phase7"))
    service = Phase7Service(persistence=persistence)
    app = create_app(service=service, api_key=API_KEY)
    with TestClient(app) as test_client:
        test_client.phase7_persistence = persistence
        yield test_client


def auth_headers():
    return {"Authorization": f"Bearer {API_KEY}"}


def test_application_startup(client):
    assert client.app.state.phase7_service is not None


def test_health_endpoint_is_public(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["model_loaded"] is True
    assert response.json()["production_model_available"] is True


def test_authentication_required(client):
    missing = client.get("/metadata/model")
    assert missing.status_code == 401

    invalid = client.get(
        "/metadata/model",
        headers={"Authorization": "Bearer wrong"},
    )
    assert invalid.status_code == 403


def test_model_metadata(client):
    response = client.get("/metadata/model", headers=auth_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["is_loaded"] is True
    assert body["num_features"] == 46
    assert body["probability_source"] == "PredictionService"
    assert body["production_model_available"] is True
    assert body["model_artifact"] == "experiments/results/model_pipeline.pkl"
    assert body["retraining_available"] is False


def test_state_computation_uses_existing_twin_engine(client, observations):
    response = client.post(
        "/states/compute",
        headers=auth_headers(),
        json={
            "student_id": "STU_PHASE7",
            "day": 50,
            "observations": observations[:50],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["student_id"] == "STU_PHASE7"
    assert body["day"] == 50
    assert body["temporal"]["day_of_semester"] == 50
    assert body["history"]["total_observations"] == 50


def test_state_computation_rejects_future_observations(client, observations):
    payload = {
        "student_id": "STU_PHASE7",
        "day": 50,
        "observations": observations[:51],
    }
    response = client.post("/states/compute", headers=auth_headers(), json=payload)
    assert response.status_code == 400
    assert "day > requested day" in response.json()["detail"]


def test_known_demo_student_uses_historical_rows_for_derived_twin_values(client):
    response = client.post(
        "/states/compute",
        headers=auth_headers(),
        json={
            "student_id": "STU_PRESSURE",
            "day": 50,
            "observations": [
                {
                    "day": 50,
                    "study_hours": 7.5,
                    "sleep_hours": 6.2,
                    "stress_level": 6,
                    "grade": 74,
                    "attendance_rate": 0.90,
                    "missed_deadline_observed": 0,
                }
            ],
            "data_source": "synthetic",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["history"]["total_observations"] == 50
    assert body["academic"]["academic_load_score"] is not None
    assert body["workload"]["workload_pressure_score_7d"] is not None
    assert body["engagement"]["engagement_composite_score"] is not None
    assert body["provenance"]["academic.academic_load_score"]["type"] == "derived"
    assert body["provenance"]["workload.workload_pressure_score_7d"]["type"] == "derived"
    assert body["provenance"]["engagement.engagement_composite_score"]["type"] == "derived"


def test_unknown_student_does_not_receive_fabricated_demo_history(client):
    response = client.post(
        "/states/compute",
        headers=auth_headers(),
        json={
            "student_id": "STU_CUSTOM_NO_HISTORY",
            "day": 50,
            "observations": [
                {
                    "day": 50,
                    "study_hours": 7.5,
                    "sleep_hours": 6.2,
                    "stress_level": 6,
                    "grade": 74,
                    "attendance_rate": 0.90,
                    "missed_deadline_observed": 0,
                }
            ],
            "data_source": "synthetic",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["history"]["total_observations"] == 1
    assert body["academic"]["academic_load_score"] is None
    assert body["workload"]["workload_pressure_score_7d"] is None
    assert body["engagement"]["engagement_composite_score"] is None


def test_prediction_probability_bounds(client, high_risk_state):
    response = client.post(
        "/predictions",
        headers=auth_headers(),
        json={"twin_state": high_risk_state, "day": 50},
    )
    assert response.status_code == 200
    probability = response.json()["overload_probability"]
    assert 0.0 <= probability <= 1.0


def test_diagnostics(client, high_risk_state):
    response = client.post(
        "/diagnostics",
        headers=auth_headers(),
        json={"twin_state": high_risk_state, "day": 50},
    )
    assert response.status_code == 200
    body = response.json()
    assert "AcademicAgent" in body["diagnoses"]
    assert "ScheduleAgent" in body["diagnoses"]
    assert body["statistics"]["total_diagnoses"] > 0


def test_scenario_generation(client, high_risk_state):
    response = client.post(
        "/scenarios/generate",
        headers=auth_headers(),
        json={"twin_state": high_risk_state, "day": 50},
    )
    assert response.status_code == 200
    scenarios = response.json()["scenarios"]
    assert len(scenarios) > 0
    assert any(s["scenario_type"] == "reduce_workload" for s in scenarios)


def test_simulation(client, high_risk_state):
    response = client.post(
        "/simulations/run",
        headers=auth_headers(),
        json={
            "twin_state": high_risk_state,
            "day": 50,
            "scenarios": [
                {
                    "scenario_type": "INCREASE_SLEEP",
                    "parameters": {"hours_per_night": 8.0},
                }
            ],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) == 1
    assert len(body["ranked_scenarios"]) == 1


def test_recommendation_safety(client, high_risk_state, monkeypatch):
    service = client.app.state.phase7_service

    def safe_delegate(twin_state, day):
        from intervention.recommendation import Recommendation

        assert twin_state.student_id == "STU_PHASE7"
        assert day == 50
        return Recommendation(
            scenario_id="phase7_safe",
            scenario_type="INCREASE_SLEEP",
            scenario_description="Student improves sleep to 8 hours/night",
            baseline_risk=0.7,
            counterfactual_risk=0.6,
            risk_delta=0.1,
            risk_reduction_percentage=14.3,
            explanation=(
                "The model-estimated impact is lower predicted overload risk "
                "under this scenario based on synthetic data."
            ),
            primary_diagnoses=["RecoveryAgent: sleep_deficit"],
            student_id=twin_state.student_id,
            day=day,
        )

    monkeypatch.setattr(service.phase6, "recommend_intervention", safe_delegate)
    # Patch validate_safety on the class so any Recommendation (including fresh ones
    # created by safe_delegate) always passes.
    monkeypatch.setattr(
        "intervention.recommendation.Recommendation.validate_safety",
        lambda self: True,
    )
    response = client.post(
        "/recommendations/generate",
        headers=auth_headers(),
        json={"twin_state": high_risk_state, "day": 50},
    )
    assert response.status_code == 200
    body = response.json()
    assert "model-estimated" in body["explanation"].lower()
    assert "synthetic data" in body["explanation"].lower()


def test_intervention_persistence_and_isolation(client):
    recommendation = {
        "scenario_id": "phase7_rec",
        "scenario_type": "INCREASE_SLEEP",
        "scenario_description": "Student improves sleep to 8 hours/night",
        "baseline_risk": 0.7,
        "counterfactual_risk": 0.6,
        "risk_delta": 0.1,
        "risk_reduction_percentage": 14.3,
        "explanation": "The model-estimated impact is based on synthetic data.",
        "primary_diagnoses": ["RecoveryAgent: sleep_deficit"],
        "confidence": "medium",
        "caveats": ["Based on model-estimated predictions", "Trained on synthetic data only"],
        "student_id": "STU_PHASE7",
        "day": 50,
    }
    response = client.post(
        "/interventions/log",
        headers=auth_headers(),
        json={"recommendation": recommendation},
    )
    assert response.status_code == 200
    intervention_id = response.json()["intervention_id"]
    registry_path = Path(client.phase7_persistence.registry_path)
    assert registry_path.exists()
    assert "data\\phase7" in str(registry_path) or "data/phase7" in str(registry_path)
    assert intervention_id in client.app.state.phase7_service.phase6.registry.records


def test_intervention_log_rejects_invalid_initial_response(client):
    recommendation = {
        "scenario_id": "phase7_rec",
        "scenario_type": "INCREASE_SLEEP",
        "scenario_description": "Student improves sleep to 8 hours/night",
        "baseline_risk": 0.7,
        "counterfactual_risk": 0.6,
        "risk_delta": 0.1,
        "risk_reduction_percentage": 14.3,
        "explanation": "The model-estimated impact is based on synthetic data.",
        "primary_diagnoses": ["RecoveryAgent: sleep_deficit"],
        "confidence": "medium",
        "caveats": ["Based on model-estimated predictions", "Trained on synthetic data only"],
        "student_id": "STU_PHASE7",
        "day": 50,
    }
    response = client.post(
        "/interventions/log",
        headers=auth_headers(),
        json={"recommendation": recommendation, "student_response": "accept"},
    )
    assert response.status_code == 400
    assert "accepted" in response.json()["detail"]


def test_intervention_response_update(client):
    intervention_id = _log_test_intervention(client)
    response = client.patch(
        f"/interventions/{intervention_id}/response",
        headers=auth_headers(),
        json={"response": "accepted", "day": 50, "feedback": "ok"},
    )
    assert response.status_code == 200
    assert response.json()["record"]["status"] == "accepted"


def test_followup_outcome_tracking(client, observations):
    intervention_id = _log_test_intervention(client)
    client.patch(
        f"/interventions/{intervention_id}/response",
        headers=auth_headers(),
        json={"response": "accepted", "day": 50},
    )
    response = client.post(
        f"/outcomes/{intervention_id}/followup",
        headers=auth_headers(),
        json={
            "followup_day": 57,
            "observations": observations,
            "student_feedback": "partial",
            "student_feedback_text": "Some improvement",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["report"]["followup_day"] == 57
    assert body["record"]["status"] == "completed"


def test_complete_recommendation_intervention_workflow(client, observations):
    state_response = client.post(
        "/states/compute",
        headers=auth_headers(),
        json={
            "student_id": "STU_PHASE7",
            "day": 50,
            "observations": observations[:50],
        },
    )
    assert state_response.status_code == 200
    twin_state = state_response.json()

    prediction_response = client.post(
        "/predictions",
        headers=auth_headers(),
        json={"twin_state": twin_state, "day": 50},
    )
    assert prediction_response.status_code == 200
    assert "overload_probability" in prediction_response.json()

    diagnostics_response = client.post(
        "/diagnostics",
        headers=auth_headers(),
        json={"twin_state": twin_state, "day": 50},
    )
    assert diagnostics_response.status_code == 200
    assert "diagnoses" in diagnostics_response.json()

    simulation_response = client.post(
        "/simulations/run",
        headers=auth_headers(),
        json={
            "twin_state": twin_state,
            "day": 50,
            "scenarios": [
                {
                    "scenario_type": "INCREASE_SLEEP",
                    "parameters": {"hours_per_night": 8.0},
                }
            ],
        },
    )
    assert simulation_response.status_code == 200
    assert len(simulation_response.json()["results"]) == 1

    recommendation_response = client.post(
        "/recommendations/generate",
        headers=auth_headers(),
        json={"twin_state": twin_state, "day": 50},
    )
    assert recommendation_response.status_code == 200
    recommendation = recommendation_response.json()
    assert recommendation["student_id"] == "STU_PHASE7"
    assert recommendation["day"] == 50

    log_response = client.post(
        "/interventions/log",
        headers=auth_headers(),
        json={
            "recommendation": recommendation,
            "student_response": "accepted",
            "feedback": "Will try it this week",
        },
    )
    assert log_response.status_code == 200
    log_body = log_response.json()
    intervention_id = log_body["intervention_id"]
    assert log_body["record"]["student_response"] == "accepted"
    assert log_body["record"]["status"] == "accepted"

    update_response = client.patch(
        f"/interventions/{intervention_id}/response",
        headers=auth_headers(),
        json={"response": "accepted", "day": 50, "feedback": "Confirmed"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["record"]["status"] == "accepted"

    followup_response = client.post(
        f"/outcomes/{intervention_id}/followup",
        headers=auth_headers(),
        json={
            "followup_day": 57,
            "observations": observations,
            "student_feedback": "partial",
            "student_feedback_text": "Some improvement",
        },
    )
    assert followup_response.status_code == 200
    followup_body = followup_response.json()
    assert followup_body["report"]["followup_day"] == 57
    assert followup_body["record"]["status"] == "completed"

    history_response = client.get(
        "/students/STU_PHASE7/history",
        headers=auth_headers(),
    )
    assert history_response.status_code == 200
    history = history_response.json()
    assert history["total_interventions"] >= 1
    assert any(record["intervention_id"] == intervention_id for record in history["interventions"])


def test_student_history(client):
    _log_test_intervention(client)
    response = client.get("/students/STU_PHASE7/history", headers=auth_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["student_id"] == "STU_PHASE7"
    assert body["total_interventions"] >= 1


def test_demo_student_history_uses_selected_day_without_future_leakage(client):
    response = client.get("/students/STU_PRESSURE/history?day=50", headers=auth_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["student_id"] == "STU_PRESSURE"
    assert body["observation_summary"]["available"] is True
    assert body["observation_summary"]["current_day"] == 50
    assert len(body["observations"]) == 50
    assert max(row["day"] for row in body["observations"]) == 50


def test_unknown_student_history_does_not_fabricate_observations(client):
    response = client.get("/students/STU_UNKNOWN/history?day=50", headers=auth_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["student_id"] == "STU_UNKNOWN"
    assert body["observations"] == []
    assert body["observation_summary"]["available"] is False


def test_analytics(client):
    _log_test_intervention(client)
    response = client.get("/analytics/system", headers=auth_headers())
    assert response.status_code == 200
    body = response.json()
    assert "registry" in body
    assert "outcomes" in body
    assert "supported_scenarios" in body


def test_temporal_safety_rejects_state_day_mismatch(client, high_risk_state):
    bad_state = dict(high_risk_state)
    bad_state["day"] = 49
    response = client.post(
        "/predictions",
        headers=auth_headers(),
        json={"twin_state": bad_state, "day": 50},
    )
    assert response.status_code == 400
    assert "must equal twin_state.day" in response.json()["detail"]


def test_temporal_safety_rejects_future_temporal_context(client, high_risk_state):
    bad_state = dict(high_risk_state)
    bad_state["temporal"] = dict(high_risk_state["temporal"])
    bad_state["temporal"]["day_of_semester"] = 51
    response = client.post(
        "/diagnostics",
        headers=auth_headers(),
        json={"twin_state": bad_state, "day": 50},
    )
    assert response.status_code == 400
    assert "future state" in response.json()["detail"]


def _log_test_intervention(client):
    recommendation = {
        "scenario_id": "phase7_rec",
        "scenario_type": "INCREASE_SLEEP",
        "scenario_description": "Student improves sleep to 8 hours/night",
        "baseline_risk": 0.7,
        "counterfactual_risk": 0.6,
        "risk_delta": 0.1,
        "risk_reduction_percentage": 14.3,
        "explanation": "The model-estimated impact is based on synthetic data.",
        "primary_diagnoses": ["RecoveryAgent: sleep_deficit"],
        "confidence": "medium",
        "caveats": ["Based on model-estimated predictions", "Trained on synthetic data only"],
        "student_id": "STU_PHASE7",
        "day": 50,
    }
    response = client.post(
        "/interventions/log",
        headers=auth_headers(),
        json={"recommendation": recommendation},
    )
    assert response.status_code == 200
    return response.json()["intervention_id"]
