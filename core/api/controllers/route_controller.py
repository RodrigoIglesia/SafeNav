from fastapi import APIRouter, Request
from domain.dto.routes import RouteRequest, RouteResponse
from domain.dto.common import ResponseMetadata
from interfaces.i_routing_service import IRoutingService
from interfaces.i_geospatial_service import IGeoService
from interfaces.i_context_service import IContextService
from datetime import datetime, timezone
from uuid import uuid4

router = APIRouter(prefix="/routes", tags=["Routes"])

@router.post("/", response_model=RouteResponse)
def create_route(request_body: RouteRequest, request: Request):
    # Create instance of services
    routing_service: IRoutingService = request.app.state.routing_service
    geospatial_service: IGeoService = request.app.state.geospatial_service
    context_service: IContextService = request.app.state.context_service
    
    # Call routing service to calculate route candidates
    candidates = routing_service.calculate_routes(request_body)
    print(f"API: Response from routing engine: {candidates} routes.")
    
    # Call geospatial engine to generate context representation of each route candidate
    context_description = geospatial_service.get_routes_context(candidates)

    # Call context service to evaluate route candidates
    scores = context_service.evaluate_routes(candidates, context_description)
    print(f"Routes scored: ", scores)

    # Prepare API response
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
