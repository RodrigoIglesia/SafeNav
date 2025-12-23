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


from fastapi import APIRouter
from domain.dto.routes import RouteRequest
from domain.dto.routes import RouteResponse
from interfaces.i_routing_service import IRoutingService

router = APIRouter(tags=["Routing"])

# TODO: Routing Engine is a mock for testing purposes.

@router.post("/", response_model=RouteResponse)
def create_route(request_body: RouteRequest, request: RouteRequest):
    """
    Process a route request and return candidate routes.
    """
    routing_service: IRoutingService = request.app.state.routing_service
    return routing_service.get_route(request_body)

