from typing import Protocol
from domain.dto.routes import RouteRequest
from domain.dto.routes import RouteCandidates, RouteScores

class IRoutingService(Protocol):
    def calculate_routes(self, request: RouteRequest) -> RouteCandidates:
        """Generate route candidates given a user request."""
        ...

    def get_route_scores(self, candidates: RouteCandidates) -> RouteScores:
        """Retrieve evaluated scores for a computed route."""
        ...
