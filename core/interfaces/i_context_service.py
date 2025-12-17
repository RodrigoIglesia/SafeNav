# core/interfaces/i_context_service.py
from typing import Protocol
from domain.dto.routes import RouteCandidates, RouteScores


class IContextService(Protocol):
    """
    Interface for contextual route analysis (CA).
    Implemented by ContextAnalyzer to evaluate comfort and safety of routes.
    """

    def evaluate_routes(self, routes: RouteCandidates) -> RouteScores:
        """
        Evaluates multiple route candidates using contextual data
        (e.g., weather, shadow zones, urban features).

        - routes: Set of candidate routes to evaluate
        - returns: RouteScores with comfort/safety values
        """
        ...