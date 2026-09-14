"""
route_controller.py
SafeNav Core - API Route Controller
--------------------------------
"""

from fastapi import APIRouter, Request
from domain.dto.routes import RouteRequest, RouteResponse
from domain.dto.common import ResponseMetadata
from interfaces.i_routing_service import IRoutingService
from interfaces.i_geospatial_service import IGeospatialService
from interfaces.i_context_service import IContextService

router = APIRouter(prefix="/routes", tags=["Routes"])

@router.post("/", response_model=RouteResponse)
def create_route(request_body: RouteRequest, request: Request):
    # Create instance of services
    routing_service: IRoutingService = request.app.state.routing_service
    geospatial_service: IGeospatialService = request.app.state.geospatial_service
    context_service: IContextService = request.app.state.context_service
    
    # Call routing service to calculate route candidates
    candidates = routing_service.calculate_routes(request_body)
    print(f"API: Response from RoutingEengine: {candidates}")
    
    # Call geospatial engine to generate context representation of each route candidate
    context_description = geospatial_service.get_routes_context(candidates)
    print(f"API: Response from Geospatial Engine: {context_description}")

    # Call context service to evaluate route candidates
    scores = context_service.evaluate_routes(candidates, context_description)
    print(f"API: Response from Context Analyzer - Routes score: {scores}")

    # Prepare API response
    metadata = ResponseMetadata(
        request_id=candidates.request_id,
        source="SafeNavCore",
    )

    return RouteResponse(
        routes=candidates,
        scores=scores,
        metadata=metadata,
    )
