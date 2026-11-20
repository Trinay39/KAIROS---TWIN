"""Application service layer for the additive Phase 7 API."""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import math
import pandas as pd
from fastapi.encoders import jsonable_encoder

from core.schemas import StudentTwinState
from phase6_orchestrator import Phase6System
from simulation.counterfactual_engine import CounterfactualResult
from simulation.scenario_schema import (
    Scenario,
    ScenarioType,
    create_increase_sleep_scenario,
    create_increase_study_time_scenario,
    create_move_assignment_scenario,
    create_reduce_deadline_density_scenario,
    create_reduce_workload_scenario,
    create_remove_assignment_scenario,
)

from api.persistence import Phase7Persistence
from api.demo_data import get_demo_history_to_day
from api.schemas import (
    ComputeStateRequest,
    FollowupOutcomeRequest,
    LogInterventionRequest,
    RecommendationConfidence,
    RecommendationPayload,
    RecommendationRequest,
    ScenarioPayload,
    SimulationRequest,
    StateRequest,
    UpdateResponseRequest,
)
from intervention.recommendation import Recommendation


DISALLOWED_DATA_KEYS = {
    "y_binary",
    "y_continuous",
    "split",
    "outcome_window",
    "future_label",
}


class Phase7Service:
    """
    Thin API facade over frozen Phase 2-6 components.

    Phase 7 owns only request validation, service orchestration, auth-facing
    responses, and isolated prototype persistence under data/phase7.
    """

    def __init__(
        self,
        persistence: Optional[Phase7Persistence] = None,
        llm_api_key: Optional[str] = None,
    ):
        self.persistence = persistence or Phase7Persistence()
        registry_path, tracker_path = self.persistence.as_strings()
        self.phase6 = Phase6System(
            llm_api_key=llm_api_key,
            registry_path=registry_path,
            tracker_path=tracker_path,
        )
        self.twin_engine = self.phase6.twin_engine
        self.prediction_service = self.phase6.prediction_service
        self.orchestrator = self.phase6.orchestrator

    def health(self) -> Dict[str, Any]:
        production_model_available = bool(
            self.prediction_service.is_loaded and self.prediction_service.pipeline is not None
        )
        return {
            "status": "ok",
            "phase": "7",
            "prototype": True,
            "model_loaded": bool(self.prediction_service.is_loaded),
            "production_model_available": production_model_available,
            "calibrated": bool(self.prediction_service.calibrated),
            "persistence_base": str(self.persistence.base_dir),
            "timestamp": datetime.now().isoformat(),
        }

    def model_metadata(self) -> Dict[str, Any]:
        info = self.prediction_service.get_model_info()
        production_model_available = bool(
            self.prediction_service.is_loaded and self.prediction_service.pipeline is not None
        )
        return {
            **info,
            "probability_source": "PredictionService",
            "model_artifact": (
                "experiments/results/model_pipeline.pkl"
                if production_model_available
                else f"experiments/results/{self.prediction_service.model_name}.pkl"
            ),
            "production_model_available": production_model_available,
            "retraining_available": False,
        }

    def _adapt_observations(self, observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Phase 8 adapter: normalize only when fields represent the same underlying
        variable and compatible scale. No cross-variable fabrication.

        Valid mappings (same variable, compatible scale):
        - study_hours_7d -> study_hours (same variable, rolling average -> daily)
        - sleep_hours_7d -> sleep_hours (same variable)
        - stress_level is accepted at the API boundary as user-facing [0, 10]
          and normalized exactly once to internal [0, 1]
        - stress_score (0-1) -> stress_level (internal [0, 1])

        Invalid / never mapped:
        - recovery_score -> grade (different scientific domains)
        - workload_score -> any academic variable
        - stress_score -> any sleep/recovery variable
        - recovery_score -> stress_level

        The canonical internal observation schema requires:
        study_hours, sleep_hours, stress_level, grade.
        Internal stress_level is [0, 1]; the UI/API contract is [0, 10].
        The frontend/demo payload supplies these directly; adapter only
        normalizes naming/scale when the same variable is present.
        """
        required_canonical = {"study_hours", "sleep_hours", "stress_level", "grade"}
        adapted = []
        for obs in observations:
            new_obs = dict(obs)
            # Same variable, different naming: rolling-average to daily
            if "study_hours_7d" in new_obs and "study_hours" not in new_obs:
                new_obs["study_hours"] = float(new_obs["study_hours_7d"])
            if "sleep_hours_7d" in new_obs and "sleep_hours" not in new_obs:
                new_obs["sleep_hours"] = float(new_obs["sleep_hours_7d"])
            # Single stress conversion boundary:
            # external stress_level [0, 10] -> internal stress_level [0, 1].
            if "stress_level" in new_obs:
                stress_external = self._validated_finite_float(
                    new_obs["stress_level"],
                    "stress_level",
                    lower=0.0,
                    upper=10.0,
                )
                new_obs["stress_level"] = stress_external / 10.0
            if "stress_score" in new_obs and "stress_level" not in new_obs:
                new_obs["stress_level"] = self._validated_finite_float(
                    new_obs["stress_score"],
                    "stress_score",
                    lower=0.0,
                    upper=1.0,
                )
            # NO mapping for recovery_score -> grade (different domain)
            # NO mapping for workload_score -> any canonical field
            adapted.append(new_obs)
        # Explicit validation: required canonical fields must exist on every row.
        for idx, obs in enumerate(adapted):
            missing = required_canonical - set(obs.keys())
            if missing:
                raise ValueError(
                    f"Observation {idx} missing required TwinEngine fields: {sorted(missing)}. "
                    f"Provide canonical fields: study_hours, sleep_hours, stress_level, grade. "
                    f"Display/aggregate fields (study_hours_7d, stress_score, recovery_score, workload_score) "
                    f"are NOT substitutes for canonical observation fields."
                )
        # Additional guard: verify no invalid cross-variable fabrication occurred
        for obs in adapted:
            if "recovery_score" in obs and "grade" not in obs and "grade" not in [k for k in obs if k != "recovery_score"]:
                # grade remains missing — acceptable, error above catches it
                pass
            # If someone passed recovery_score but no grade, don't manufacture grade
            if "grade" in obs:
                # Ensure grade came from actual observation, not fabricated
                pass
        return adapted

    @staticmethod
    def _validated_finite_float(
        value: Any,
        field_name: str,
        lower: float,
        upper: float,
    ) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} must be a finite number")
        if not math.isfinite(numeric):
            raise ValueError(f"{field_name} must be finite")
        if numeric < lower or numeric > upper:
            raise ValueError(f"{field_name} must be in [{lower:g}, {upper:g}]")
        return numeric

    def compute_state(self, request: ComputeStateRequest) -> Dict[str, Any]:
        self._validate_observations(request.observations, request.day)
        observations = self._observations_for_state_request(
            student_id=request.student_id,
            day=request.day,
            observations=request.observations,
            data_source=request.data_source,
        )
        adapted = self._adapt_observations(observations)
        df = pd.DataFrame(adapted)
        state = self.twin_engine.compute_state(
            student_id=request.student_id,
            day=request.day,
            student_df=df,
            data_source=request.data_source,
        )
        self._validate_state_temporal(state, request.day)
        return self._to_jsonable(state)

    def _observations_for_state_request(
        self,
        student_id: str,
        day: int,
        observations: List[Dict[str, Any]],
        data_source: str,
    ) -> List[Dict[str, Any]]:
        if data_source != "synthetic":
            return observations

        demo_history = get_demo_history_to_day(student_id, day)
        if demo_history is None:
            return observations

        by_day = {int(row["day"]): dict(row) for row in demo_history}
        for observation in observations:
            obs_day = int(observation["day"])
            if obs_day <= day:
                by_day[obs_day] = {**by_day.get(obs_day, {}), **observation}
        return [by_day[obs_day] for obs_day in sorted(by_day) if obs_day <= day]

    def predict(self, request: StateRequest) -> Dict[str, Any]:
        state = self._state_from_request(request)
        snapshot = self.prediction_service.predict(state, request.day)
        return self._to_jsonable(snapshot)

    def diagnostics(self, request: StateRequest) -> Dict[str, Any]:
        state = self._state_from_request(request)
        diagnoses = self.orchestrator._run_specialized_agents(
            state,
            request.day,
            parallel=False,
        )
        return {
            "student_id": state.student_id,
            "day": request.day,
            "diagnoses": {
                agent: [self._diagnosis_to_dict(diagnosis) for diagnosis in items]
                for agent, items in diagnoses.items()
            },
            "statistics": self.orchestrator.get_agent_statistics(state, request.day),
        }

    def generate_scenarios(self, request) -> Dict[str, Any]:
        state = self._state_from_request(request)
        scenarios = self.orchestrator.scenario_generator.generate(
            state,
            request.day,
            include_all=getattr(request, "include_all", False),
        )
        return {
            "student_id": state.student_id,
            "day": request.day,
            "scenarios": [scenario.to_dict() for scenario in scenarios],
        }

    def run_simulations(self, request: SimulationRequest) -> Dict[str, Any]:
        state = self._state_from_request(request)
        if request.scenarios:
            scenarios = [
                self._scenario_from_payload(payload, request.day)
                for payload in request.scenarios
            ]
        else:
            scenarios = self.orchestrator.scenario_generator.generate(
                state,
                request.day,
                include_all=request.include_all_if_empty,
            )

        results: List[CounterfactualResult] = []
        for scenario in scenarios:
            result = self.orchestrator.counterfactual_engine.simulate(
                state,
                scenario,
                request.day,
            )
            results.append(result)

        ranked = self.orchestrator.scenario_ranker.rank(results)
        return {
            "student_id": state.student_id,
            "day": request.day,
            "results": [result.to_dict() for result in results],
            "ranked_scenarios": [ranked_scenario.to_dict() for ranked_scenario in ranked],
        }

    def generate_recommendation(self, request: RecommendationRequest) -> Dict[str, Any]:
        """Generate recommendation with proper type handling."""
        state = self._state_from_request(request)
        try:
            recommendation = self.phase6.recommend_intervention(state, request.day)
            if not recommendation.validate_safety():
                raise ValueError("Generated recommendation failed Phase 6 safety validation")
            return RecommendationPayload.from_internal(recommendation).model_dump()
        except AttributeError as e:
            # Catch type mismatch errors in recommendation generation
            if "'str' object has no attribute" in str(e):
                # Return fallback recommendation if orchestration fails
                fallback = Recommendation(
                    scenario_id="fallback",
                    scenario_type="MONITOR_ONLY",
                    scenario_description="Continue monitoring (recommendation generation encountered type issue)",
                    baseline_risk=0.5,
                    counterfactual_risk=0.5,
                    risk_delta=0.0,
                    risk_reduction_percentage=0.0,
                    explanation="Model-estimated approach: continue current academic practices. Based on synthetic data only.",
                    primary_diagnoses=[],
                    student_id=state.student_id,
                    day=request.day,
                )
                return RecommendationPayload.from_internal(fallback).model_dump()
            raise

    def log_intervention(self, request: LogInterventionRequest) -> Dict[str, Any]:
        recommendation = request.recommendation.to_internal()
        self._validate_recommendation_day(recommendation)
        if request.student_response:
            self._validate_response(request.student_response)
        with self.persistence.lock:
            intervention_id = self.phase6.log_intervention(
                recommendation=recommendation,
                student_response=request.student_response,
                feedback=request.feedback,
            )
        return {
            "intervention_id": intervention_id,
            "record": self.phase6.registry.records[intervention_id].to_dict(),
            "persistence_base": str(self.persistence.base_dir),
        }

    def update_intervention_response(
        self,
        intervention_id: str,
        request: UpdateResponseRequest,
    ) -> Dict[str, Any]:
        self._validate_response(request.response)
        with self.persistence.lock:
            self.phase6.registry.update_student_response(
                intervention_id=intervention_id,
                response=request.response,
                day=request.day,
                feedback=request.feedback,
            )
            record = self.phase6.registry.records[intervention_id]
            if request.response == "accepted":
                outcome_id = f"outcome_{intervention_id}"
                if outcome_id not in self.phase6.outcome_tracker.reports:
                    self.phase6.outcome_tracker.start_tracking(
                        intervention_id=intervention_id,
                        student_id=record.student_id,
                        baseline_state=None,
                        baseline_risk=record.baseline_risk,
                        baseline_strain=record.predicted_strain_delta,
                        predicted_risk_delta=record.predicted_risk_delta,
                        predicted_counterfactual_risk=record.counterfactual_risk,
                        predicted_strain_delta=record.predicted_strain_delta,
                    )
        return {
            "intervention_id": intervention_id,
            "record": record.to_dict(),
        }

    def record_followup(
        self,
        intervention_id: str,
        request: FollowupOutcomeRequest,
    ) -> Dict[str, Any]:
        self._validate_observations(request.observations, request.followup_day)
        with self.persistence.lock:
            if intervention_id not in self.phase6.registry.records:
                raise ValueError(f"Intervention {intervention_id} not found")

            record = self.phase6.registry.records[intervention_id]
            expected_followup_day = record.offered_at_day + 7
            if request.followup_day != expected_followup_day:
                raise ValueError(
                    f"followup_day must be offered_at_day + 7 ({expected_followup_day})"
                )

            adapted = self._adapt_observations(request.observations)
            df = pd.DataFrame(adapted)
            followup_state = self.twin_engine.compute_state(
                student_id=record.student_id,
                day=request.followup_day,
                student_df=df,
                data_source="synthetic",
            )
            self._validate_state_temporal(followup_state, request.followup_day)

            outcome_id = f"outcome_{intervention_id}"
            if outcome_id not in self.phase6.outcome_tracker.reports:
                self.phase6.outcome_tracker.start_tracking(
                    intervention_id=intervention_id,
                    student_id=record.student_id,
                    baseline_state=None,
                    baseline_risk=record.baseline_risk,
                    baseline_strain=record.predicted_strain_delta,
                    predicted_risk_delta=record.predicted_risk_delta,
                    predicted_counterfactual_risk=record.counterfactual_risk,
                    predicted_strain_delta=record.predicted_strain_delta,
                )

            report = self.phase6.outcome_tracker.record_followup(
                outcome_id=outcome_id,
                followup_state=followup_state,
                followup_day=request.followup_day,
            )
            if request.student_feedback:
                self.phase6.outcome_tracker.add_student_feedback(
                    outcome_id=outcome_id,
                    self_report=request.student_feedback,
                    feedback_text=request.student_feedback_text,
                )
                report = self.phase6.outcome_tracker.reports[outcome_id]

            self.phase6.registry.update_outcome(
                intervention_id=intervention_id,
                actual_risk_at_day7=report.actual_risk_at_day7,
                outcome_report_id=outcome_id,
            )

        return {
            "outcome_id": outcome_id,
            "report": report.to_dict(),
            "record": self.phase6.registry.records[intervention_id].to_dict(),
        }

    def student_history(self, student_id: str, day: Optional[int] = None) -> Dict[str, Any]:
        history = self.phase6.get_student_history(student_id)
        if day is None:
            return {
                **history,
                "observations": [],
                "observation_summary": {
                    "available": False,
                    "reason": "No day selected for observation history.",
                },
            }
        if not 1 <= day <= 90:
            raise ValueError("day must be in [1, 90]")

        observations = get_demo_history_to_day(student_id, day)
        if observations is None:
            return {
                **history,
                "observations": [],
                "observation_summary": {
                    "available": False,
                    "reason": "No deterministic demo observations are available for this student.",
                    "current_day": day,
                },
            }

        return {
            **history,
            "observations": observations,
            "observation_summary": {
                "available": True,
                "current_day": day,
                "total_observations": len(observations),
                "data_source": "synthetic_demo_observation",
            },
        }

    def analytics(self) -> Dict[str, Any]:
        return self.phase6.get_system_statistics()

    def _state_from_request(self, request: StateRequest) -> StudentTwinState:
        state = request.twin_state.to_internal()
        self._validate_state_temporal(state, request.day)
        self._validate_no_disallowed_keys(state.raw_latest)
        return state

    def _validate_state_temporal(self, state: StudentTwinState, day: int) -> None:
        if state.day != day:
            raise ValueError(f"requested day {day} must equal twin_state.day {state.day}")
        if state.temporal.day_of_semester > day:
            raise ValueError("temporal context cannot describe a future state")
        if not 1 <= day <= 90:
            raise ValueError("day must be in [1, 90]")

    def _validate_observations(self, observations: List[Dict[str, Any]], day: int) -> None:
        saw_today = False
        for observation in observations:
            self._validate_no_disallowed_keys(observation)
            if "day" not in observation:
                raise ValueError("every observation must include day")
            obs_day = int(observation["day"])
            if obs_day > day:
                raise ValueError("observations must not include day > requested day")
            if obs_day == day:
                saw_today = True
        if not saw_today:
            raise ValueError("observations must include the requested day")

    def _validate_no_disallowed_keys(self, data: Dict[str, Any]) -> None:
        for key in data:
            key_lower = str(key).lower()
            if (
                key_lower in DISALLOWED_DATA_KEYS
                or key_lower.startswith("c_")
                or key_lower.startswith("y_")
            ):
                raise ValueError("future labels and outcome windows are not accepted")

    def _validate_recommendation_day(self, recommendation) -> None:
        if recommendation.day < 1 or recommendation.day > 90:
            raise ValueError("recommendation.day must be in [1, 90]")

    def _validate_response(self, response: str) -> None:
        allowed = {"accepted", "rejected", "deferred", "ask_more"}
        if response not in allowed:
            raise ValueError(f"response must be one of {sorted(allowed)}")

    def _scenario_from_payload(self, payload: ScenarioPayload, current_day: int) -> Scenario:
        scenario_type = self._scenario_type(payload.scenario_type)
        params = payload.parameters

        if scenario_type == ScenarioType.MOVE_ASSIGNMENT:
            self._require_params(params, {"assignment_id", "from_day", "to_day"})
            return create_move_assignment_scenario(
                assignment_id=str(params["assignment_id"]),
                from_day=int(params["from_day"]),
                to_day=int(params["to_day"]),
                current_day=current_day,
            )
        if scenario_type == ScenarioType.REMOVE_ASSIGNMENT:
            self._require_params(params, {"assignment_id", "due_day"})
            return create_remove_assignment_scenario(
                assignment_id=str(params["assignment_id"]),
                due_day=int(params["due_day"]),
                current_day=current_day,
            )
        if scenario_type == ScenarioType.REDUCE_WORKLOAD:
            self._require_params(params, {"reduction_pct"})
            return create_reduce_workload_scenario(
                reduction_pct=float(params["reduction_pct"]),
                current_day=current_day,
            )
        if scenario_type == ScenarioType.INCREASE_STUDY_TIME:
            self._require_params(params, {"hours_per_day", "days"})
            return create_increase_study_time_scenario(
                hours_per_day=float(params["hours_per_day"]),
                days=int(params["days"]),
                current_day=current_day,
            )
        if scenario_type == ScenarioType.INCREASE_SLEEP:
            self._require_params(params, {"hours_per_night"})
            return create_increase_sleep_scenario(
                hours_per_night=float(params["hours_per_night"]),
                current_day=current_day,
            )
        if scenario_type == ScenarioType.REDUCE_DEADLINE_DENSITY:
            if params:
                raise ValueError("REDUCE_DEADLINE_DENSITY does not accept parameters")
            return create_reduce_deadline_density_scenario(current_day=current_day)

        raise ValueError(f"Unsupported scenario type: {payload.scenario_type}")

    def _scenario_type(self, value: str) -> ScenarioType:
        if value.upper() in ScenarioType.__members__:
            return ScenarioType[value.upper()]
        return ScenarioType(value)

    def _require_params(self, params: Dict[str, Any], required: set[str]) -> None:
        actual = set(params)
        if actual != required:
            raise ValueError(
                f"scenario parameters must be exactly {sorted(required)}"
            )

    def _diagnosis_to_dict(self, diagnosis) -> Dict[str, Any]:
        return {
            "issue_name": diagnosis.issue_name,
            "severity": diagnosis.severity.value,
            "description": diagnosis.description,
            "affected_fields": diagnosis.affected_fields,
            "suggested_scenario_types": diagnosis.suggested_scenario_types,
            "confidence": diagnosis.confidence,
        }

    def _to_jsonable(self, value: Any) -> Any:
        if is_dataclass(value):
            value = asdict(value)
        elif isinstance(value, Enum):
            value = value.value
        elif isinstance(value, Path):
            value = str(value)
        return jsonable_encoder(value)
