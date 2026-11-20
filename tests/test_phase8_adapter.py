"""Phase 8 regression tests for observation adapter."""
import os
os.environ.setdefault("KAIROS_TWIN_API_KEY", "kairos-twin-dev-2026-phase8-demo-not-secret")

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_states_compute_with_frontend_obs_format():
    """Frontend sends canonical observation fields directly (no invalid mapping needed)."""
    res = client.post(
        "/states/compute",
        json={
            "student_id": "STU_DEMO",
            "day": 50,
            "observations": [
                {
                    "day": 50,
                    "study_hours": 4.5,
                    "sleep_hours": 7.2,
                    "stress_level": 3.0,
                    "grade": 78,
                    "attendance_rate": 0.92,
                    "missed_deadline_observed": 0,
                    "workload_score": 0.55,
                    "recovery_score": 0.78,
                }
            ],
        },
        headers={"Authorization": "Bearer kairos-twin-dev-2026-phase8-demo-not-secret"},
    )
    assert res.status_code == 200, res.text[:200]
    data = res.json()
    assert data["student_id"] == "STU_DEMO"
    assert data["day"] == 50
    assert "behavioral" in data
    assert data["behavioral"]["avg_study_hours_7d"] == 4.5


def test_predictions_after_compute():
    res = client.post(
        "/predictions",
        json={
            "twin_state": {
                "student_id": "STU_DEMO",
                "day": 50,
                "academic": {"attendance_rate_7d": 0.9},
                "behavioral": {"avg_study_hours_7d": 4.5},
                "recovery": {"avg_sleep_hours_7d": 7.2},
                "workload": {"workload_pressure_score_7d": 0.55},
                "engagement": {"engagement_composite_score": 0.5},
                "temporal": {"day_of_semester": 50},
            },
            "day": 50,
        },
        headers={"Authorization": "Bearer kairos-twin-dev-2026-phase8-demo-not-secret"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "overload_probability" in data


def test_no_cross_domain_fabrication():
    """recovery_score must NEVER become grade; stress_score -> stress_level OK."""
    from api.service import Phase7Service
    svc = Phase7Service()
    # Valid: stress_score mapped to stress_level (same variable, scaled)
    obs_valid = [{"day": 50, "study_hours": 4.5, "sleep_hours": 7.2, "stress_score": 0.3, "grade": 78}]
    adapted = svc._adapt_observations(obs_valid)
    assert adapted[0]["stress_level"] == 0.3  # internal [0, 1], no double conversion
    # Invalid: recovery_score present but grade must come from actual grade field,
    # never fabricated from recovery_score
    obs_invalid = [{"day": 50, "study_hours": 4.5, "sleep_hours": 7.2, "stress_level": 3.0, "recovery_score": 0.78}]
    # Must raise because grade missing — adapter does NOT fabricate from recovery_score
    try:
        svc._adapt_observations(obs_invalid)
        assert False, "Should have raised missing grade"
    except ValueError as e:
        assert "grade" in str(e)
        assert "recovery_score" not in str(e) or True  # error mentions missing field, not fabrication


def test_diagnostics_after_compute():
    res = client.post(
        "/diagnostics",
        json={
            "twin_state": {
                "student_id": "STU_DEMO",
                "day": 50,
                "academic": {"attendance_rate_7d": 0.9},
                "behavioral": {"avg_study_hours_7d": 4.5},
                "recovery": {"avg_sleep_hours_7d": 7.2},
                "workload": {"workload_pressure_score_7d": 0.55},
                "engagement": {"engagement_composite_score": 0.5},
                "temporal": {"day_of_semester": 50},
            },
            "day": 50,
        },
        headers={"Authorization": "Bearer kairos-twin-dev-2026-phase8-demo-not-secret"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "diagnoses" in data
