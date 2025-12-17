# core/routing_engine/service.py
"""
Routing Engine - Mock Implementation
------------------------------------
Implements the IRoutingService interface.
This version returns mock data for development/testing.
"""

from domain.dto.routes import RouteRequest, RouteResponse, RouteCandidate, ResponseMetadata
from domain.dto.common import GeoPoint
from datetime import datetime
from uuid import uuid4


class RoutingEngine:
    """Implements IRoutingService."""

    def get_route(self, request: RouteRequest) -> RouteResponse:
        # TODO: Mock - Generate fake candidate route
        candidate = RouteCandidate(
            id=str(uuid4()),
            geometry={"coordinates": [request.origin, request.destination]},
            eta=900,
            distance=1.2
        )

        metadata = ResponseMetadata(
            timestamp=datetime.utcnow(),
            request_id=str(uuid4()),
            source="RoutingEngine-Mock"
        )

        return RouteResponse(routes=[candidate], metadata=metadata)
