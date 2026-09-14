from typing import Protocol

from domain.dto.routes import RouteCandidates, RouteRequest


class IRoutingService(Protocol):
    """
    Provides route candidate generation.

    Implemented by Routing Engine (RE).
    """

    def calculate_routes(
        self,
        request: RouteRequest,
    ) -> RouteCandidates:
        """
        Generate route candidates for the supplied route request.
        """
        ...