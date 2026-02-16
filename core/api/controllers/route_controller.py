from fastapi import APIRouter, Request
from domain.dto.routes import RouteRequest, RouteResponse
from domain.dto.common import ResponseMetadata
from interfaces.i_routing_service import IRoutingService
from datetime import datetime, timezone
from uuid import uuid4

router = APIRouter(prefix="/routes", tags=["Routes"])

@router.post("/", response_model=RouteResponse)
def create_route(request_body: RouteRequest, request: Request):
    routing_service: IRoutingService = request.app.state.routing_service

    candidates = routing_service.calculate_routes(request_body)
    scores = routing_service.get_route_scores(candidates)

    metadata = ResponseMetadata(
        timestamp=datetime.now(timezone.utc),
        request_id=str(uuid4()),
        source="SafeNavCore",
    )

    return RouteResponse(
        routes=candidates,
        scores=scores,
        metadata=metadata,
    )
