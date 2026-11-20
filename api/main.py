"""FastAPI entry point for the Phase 7 research prototype API."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    ComputeStateRequest,
    FollowupOutcomeRequest,
    GenerateScenariosRequest,
    LogInterventionRequest,
    RecommendationRequest,
    SimulationRequest,
    StateRequest,
    UpdateResponseRequest,
)
from api.security import require_api_key_factory
from api.service import Phase7Service


def create_app(
    service: Optional[Phase7Service] = None,
    api_key: Optional[str] = None,
) -> FastAPI:
    app = FastAPI(
        title="KAIROS-TWIN Phase 7 API",
        version="0.1.0",
        description="Research prototype API layer over frozen Phase 2-6 components.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Authorization", "Content-Type"],
    )

    app.state.phase7_service = service or Phase7Service()
    require_api_key = require_api_key_factory(api_key)

    def get_service() -> Phase7Service:
        return app.state.phase7_service

    def handle_error(error: Exception) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    @app.get("/health")
    def health(svc: Phase7Service = Depends(get_service)):
        return svc.health()

    @app.get("/metadata/model", dependencies=[Depends(require_api_key)])
    def model_metadata(svc: Phase7Service = Depends(get_service)):
        return svc.model_metadata()

    @app.post("/states/compute", dependencies=[Depends(require_api_key)])
    def compute_state(
        request: ComputeStateRequest,
        svc: Phase7Service = Depends(get_service),
    ):
        try:
            return svc.compute_state(request)
        except Exception as error:
            raise handle_error(error)

    @app.post("/predictions", dependencies=[Depends(require_api_key)])
    def predictions(
        request: StateRequest,
        svc: Phase7Service = Depends(get_service),
    ):
        try:
            return svc.predict(request)
        except Exception as error:
            raise handle_error(error)

    @app.post("/diagnostics", dependencies=[Depends(require_api_key)])
    def diagnostics(
        request: StateRequest,
        svc: Phase7Service = Depends(get_service),
    ):
        try:
            return svc.diagnostics(request)
        except Exception as error:
            raise handle_error(error)

    @app.post("/scenarios/generate", dependencies=[Depends(require_api_key)])
    def generate_scenarios(
        request: GenerateScenariosRequest,
        svc: Phase7Service = Depends(get_service),
    ):
        try:
            return svc.generate_scenarios(request)
        except Exception as error:
            raise handle_error(error)

    @app.post("/simulations/run", dependencies=[Depends(require_api_key)])
    def run_simulations(
        request: SimulationRequest,
        svc: Phase7Service = Depends(get_service),
    ):
        try:
            return svc.run_simulations(request)
        except Exception as error:
            raise handle_error(error)

    @app.post("/recommendations/generate", dependencies=[Depends(require_api_key)])
    def generate_recommendation(
        request: RecommendationRequest,
        svc: Phase7Service = Depends(get_service),
    ):
        try:
            return svc.generate_recommendation(request)
        except Exception as error:
            raise handle_error(error)

    @app.post("/interventions/log", dependencies=[Depends(require_api_key)])
    def log_intervention(
        request: LogInterventionRequest,
        svc: Phase7Service = Depends(get_service),
    ):
        try:
            return svc.log_intervention(request)
        except Exception as error:
            raise handle_error(error)

    @app.patch("/interventions/{intervention_id}/response", dependencies=[Depends(require_api_key)])
    def update_intervention_response(
        intervention_id: str,
        request: UpdateResponseRequest,
        svc: Phase7Service = Depends(get_service),
    ):
        try:
            return svc.update_intervention_response(intervention_id, request)
        except Exception as error:
            raise handle_error(error)

    @app.post("/outcomes/{intervention_id}/followup", dependencies=[Depends(require_api_key)])
    def record_followup(
        intervention_id: str,
        request: FollowupOutcomeRequest,
        svc: Phase7Service = Depends(get_service),
    ):
        try:
            return svc.record_followup(intervention_id, request)
        except Exception as error:
            raise handle_error(error)

    @app.get("/students/{student_id}/history", dependencies=[Depends(require_api_key)])
    def student_history(
        student_id: str,
        day: Optional[int] = None,
        svc: Phase7Service = Depends(get_service),
    ):
        try:
            return svc.student_history(student_id, day)
        except Exception as error:
            raise handle_error(error)

    @app.get("/analytics/system", dependencies=[Depends(require_api_key)])
    def analytics(svc: Phase7Service = Depends(get_service)):
        return svc.analytics()

    return app


app = create_app()
