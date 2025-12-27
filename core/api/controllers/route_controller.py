#TODO: Implementar contrato para obtener el mapa a visualizar

"""
SafeNav Core - Route Controller
-------------------------------
This module defines the HTTP endpoints exposed by the SafeNav Core API Layer
for route management. It provides entry points to request new routes and 
retrieve previously generated route results.

The controller acts as a thin presentation layer between the external API
interface (FastAPI) and the internal routing logic implemented in the 
Routing Engine.

Endpoints:
    POST /routes
        Accepts a RouteRequest (origin, destination, and preferences)
        and returns a RouteResponse containing candidate routes with 
        contextual scores.
"""


from fastapi import APIRouter, Request
from domain.dto.routes import RouteRequest, RouteResponse
from domain.dto.common import ResponseMetadata
from interfaces.i_routing_service import IRoutingService
from datetime import datetime, timezone
from uuid import uuid4

router = APIRouter(prefix="/routes", tags=["Routes"])

@router.post("/", response_model=RouteResponse)
def create_route(request_body: RouteRequest, request: Request):
    """
    Process a route request and return candidate routes.
    """
    routing_service: IRoutingService = request.app.state.routing_service
    candidates =  routing_service.calculate_routes(request_body)
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


